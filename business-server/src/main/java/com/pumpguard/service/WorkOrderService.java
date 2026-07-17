package com.pumpguard.service;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 工单服务
 *
 * 与架构说明书 3.3.1 工单自动生成与路由一致
 */
@Service
public class WorkOrderService {

    // Demo 阶段内存存储（生产环境用 JPA Repository）
    private final Map<String, Map<String, Object>> orders = new ConcurrentHashMap<>();

    /**
     * 从告警自动生成工单
     */
    public Map<String, Object> createFromAlert(String deviceId, Map<String, Object> hiResult,
                                                Map<String, Object> faultResult, Map<String, Object> rcaResult) {
        String id = "WO-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();

        double hi = ((Number) hiResult.getOrDefault("health_index", 50)).doubleValue();
        String severity = hi < 30 ? "P0" : hi < 50 ? "P1" : hi < 70 ? "P2" : "P3";

        // 提取故障信息
        String faultType = "待确认";
        double probability = 0;
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> predictions = (List<Map<String, Object>>) (Object) faultResult.getOrDefault("predictions", List.of());
        if (!predictions.isEmpty()) {
            Map<String, Object> top = predictions.get(0);
            faultType = (String) top.getOrDefault("fault_type", "待确认");
            probability = ((Number) top.getOrDefault("probability", 0)).doubleValue();
        }

        // 提取根因
        String suggestedAction = "";
        String spareParts = "";
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> rootCauses = (List<Map<String, Object>>) (Object) rcaResult.getOrDefault("root_causes", List.of());
        if (!rootCauses.isEmpty()) {
            Map<String, Object> topRca = rootCauses.get(0);
            suggestedAction = (String) topRca.getOrDefault("suggested_action", "");
            @SuppressWarnings("unchecked")
            List<String> parts = (List<String>) (Object) topRca.getOrDefault("spare_parts", List.of());
            spareParts = String.join(",", parts);
        }

        // 匹配工程师（Demo：简单轮转）
        String engineer = matchEngineer(deviceId);

        Map<String, Object> order = new LinkedHashMap<>();
        order.put("id", id);
        order.put("device_id", deviceId);
        order.put("fault_type", faultType);
        order.put("severity", severity);
        order.put("description", "AI 预测故障: " + faultType + "（置信度 " + Math.round(probability * 100) + "%）");
        order.put("suggested_action", suggestedAction);
        order.put("spare_parts", spareParts);
        order.put("assigned_engineer", engineer);
        order.put("status", "pending");
        order.put("ai_diagnosis_correct", null);
        order.put("actual_fault", null);
        order.put("created_at", LocalDateTime.now().toString());
        order.put("updated_at", LocalDateTime.now().toString());

        orders.put(id, order);
        System.out.println("[WorkOrder] 自动生成工单: " + id + " → " + deviceId + " (" + faultType + ")");
        return order;
    }

    /**
     * 工程师匹配（Demo：最近邻）
     */
    private String matchEngineer(String deviceId) {
        String[] engineers = {"张三", "李四", "王五", "赵六"};
        return engineers[Math.abs(deviceId.hashCode()) % engineers.length];
    }

    /**
     * 记录维修反馈
     */
    public void recordFeedback(String workOrderId, boolean isCorrect, String actualFault) {
        Map<String, Object> order = orders.get(workOrderId);
        if (order != null) {
            order.put("status", "completed");
            order.put("ai_diagnosis_correct", isCorrect);
            order.put("actual_fault", actualFault);
            order.put("completed_at", LocalDateTime.now().toString());
            order.put("updated_at", LocalDateTime.now().toString());
        }
    }

    /** 工单列表 */
    public List<Map<String, Object>> listOrders() {
        return new ArrayList<>(orders.values());
    }
}
