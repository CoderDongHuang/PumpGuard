package com.pumpguard.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * Kafka 消费者服务
 *
 * 监听 Topic:
 *   - pump.sensor.data     传感器数据 → 触发 HI 计算
 *   - alert.triggered      告警事件 → 存储 + 推送飞书
 *   - maintenance.feedback 维修反馈 → 触发模型更新
 */
@Service
public class KafkaConsumerService {

    private final AIClientService aiClient;
    private final DeviceService deviceService;
    private final WorkOrderService workOrderService;
    private final AlertService alertService;
    private final ObjectMapper mapper = new ObjectMapper();

    public KafkaConsumerService(AIClientService aiClient, DeviceService deviceService,
                                WorkOrderService workOrderService, AlertService alertService) {
        this.aiClient = aiClient;
        this.deviceService = deviceService;
        this.workOrderService = workOrderService;
        this.alertService = alertService;
    }

    /**
     * 消费传感器数据 → 触发 AI 分析
     */
    @KafkaListener(topics = "pump.sensor.data", groupId = "pumpguard-business")
    public void onSensorData(String message) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> data = mapper.readValue(message, Map.class);
            String deviceId = (String) data.get("device_id");

            // 更新设备缓存
            deviceService.upsertDevice(data);

            // 调用 AI Engine 计算 HI
            Map<String, Object> hiRequest = Map.of(
                "device_id", deviceId,
                "pump_specs", extractPumpSpecs(deviceId),
                "current_data", data
            );
            Map<String, Object> hiResult = aiClient.computeHI(hiRequest);

            double hi = ((Number) hiResult.get("health_index")).doubleValue();

            // HI < 70 → 触发告警 + 工单
            if (hi < 70) {
                // 根因分析
                Map<String, Object> rcaRequest = Map.of("device_id", deviceId, "current_data", data);
                Map<String, Object> rcaResult = aiClient.analyzeRootCause(rcaRequest);

                // 故障预测
                Map<String, Object> faultRequest = Map.of("device_id", deviceId, "sensor_sequence", java.util.List.of(data));
                Map<String, Object> faultResult = aiClient.predictFault(faultRequest);

                // 生成告警
                alertService.createAlert(deviceId, hiResult, faultResult, rcaResult);

                // HI < 50 → 自动生成工单
                if (hi < 50) {
                    workOrderService.createFromAlert(deviceId, hiResult, faultResult, rcaResult);
                }
            }
        } catch (Exception e) {
            System.err.println("[KafkaConsumer] 传感器数据处理失败: " + e.getMessage());
        }
    }

    /**
     * 消费告警事件 → 存储
     */
    @KafkaListener(topics = "alert.triggered", groupId = "pumpguard-business")
    public void onAlertTriggered(String message) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> alert = mapper.readValue(message, Map.class);
            System.out.println("[KafkaConsumer] 收到告警: " + alert.get("device_id"));
        } catch (Exception e) {
            System.err.println("[KafkaConsumer] 告警处理失败: " + e.getMessage());
        }
    }

    /**
     * 消费维修反馈 → 触发 AI 模型更新
     */
    @KafkaListener(topics = "maintenance.feedback", groupId = "pumpguard-business")
    public void onFeedback(String message) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> feedback = mapper.readValue(message, Map.class);
            System.out.println("[KafkaConsumer] 收到维修反馈: " + feedback.get("device_id"));

            // 转发给 AI Engine
            aiClient.submitFeedback(feedback);

            // 更新工单状态
            String workOrderId = (String) feedback.get("work_order_id");
            Boolean isCorrect = (Boolean) feedback.get("is_correct");
            String actualFault = (String) feedback.get("actual_fault");
            if (workOrderId != null) {
                workOrderService.recordFeedback(workOrderId, isCorrect != null && isCorrect, actualFault);
            }
        } catch (Exception e) {
            System.err.println("[KafkaConsumer] 反馈处理失败: " + e.getMessage());
        }
    }

    private Map<String, Object> extractPumpSpecs(String deviceId) {
        // Demo: 返回默认参数
        return Map.of(
            "rated_flow", 50,
            "rated_head", 30,
            "rated_efficiency", 0.75,
            "rated_power", 5.5,
            "rated_speed", 2900
        );
    }
}
