package com.pumpguard.service;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 告警服务
 *
 * 与架构说明书 3.3 决策层对齐
 */
@Service
public class AlertService {

    private final Map<String, Map<String, Object>> alerts = new ConcurrentHashMap<>();

    /**
     * 创建告警
     */
    public Map<String, Object> createAlert(String deviceId, Map<String, Object> hiResult,
                                            Map<String, Object> faultResult, Map<String, Object> rcaResult) {
        String id = "ALT-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();

        double hi = ((Number) hiResult.getOrDefault("health_index", 50)).doubleValue();
        String severity = hi < 30 ? "P0" : hi < 50 ? "P1" : hi < 70 ? "P2" : "P3";

        // 提取故障预测
        String faultType = "待分析";
        double probability = 0;
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> predictions = (List<Map<String, Object>>) (Object) faultResult.getOrDefault("predictions", List.of());
        if (!predictions.isEmpty()) {
            Map<String, Object> top = predictions.get(0);
            faultType = (String) top.getOrDefault("fault_type", "待分析");
            probability = ((Number) top.getOrDefault("probability", 0)).doubleValue();
        }

        // 提取建议
        String suggestedAction = "";
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> rootCauses = (List<Map<String, Object>>) (Object) rcaResult.getOrDefault("root_causes", List.of());
        if (!rootCauses.isEmpty()) {
            Map<String, Object> top = rootCauses.get(0);
            suggestedAction = (String) top.getOrDefault("suggested_action", "");
        }

        Map<String, Object> alert = new LinkedHashMap<>();
        alert.put("id", id);
        alert.put("device_id", deviceId);
        alert.put("fault_type", faultType);
        alert.put("health_index", hi);
        alert.put("probability", Math.round(probability * 100));
        alert.put("severity", severity);
        alert.put("suggested_action", suggestedAction);
        alert.put("acknowledged", false);
        alert.put("created_at", LocalDateTime.now().toString());

        alerts.put(id, alert);
        System.out.println("[Alert] 告警生成: " + id + " → " + deviceId + " HI=" + hi + " " + faultType);
        return alert;
    }

    /** 告警列表 */
    public List<Map<String, Object>> listAlerts() {
        return new ArrayList<>(alerts.values());
    }
}
