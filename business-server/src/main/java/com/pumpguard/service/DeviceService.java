package com.pumpguard.service;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.query.FluxTable;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 设备管理服务（Demo 版 — 内存存储）
 *
 * 生产环境应使用 PostgreSQL + JPA Repository
 */
@Service
public class DeviceService {

    @Value("${influxdb.url}")
    private String influxUrl;

    @Value("${influxdb.token}")
    private String influxToken;

    @Value("${influxdb.org}")
    private String influxOrg;

    @Value("${influxdb.bucket}")
    private String influxBucket;

    private InfluxDBClient influxClient;

    // Demo 阶段内存存储
    private final Map<String, Map<String, Object>> devices = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        try {
            influxClient = InfluxDBClientFactory.create(influxUrl, influxToken.toCharArray(), influxOrg, influxBucket);
            System.out.println("[DeviceService] InfluxDB 已连接");
        } catch (Exception e) {
            System.err.println("[DeviceService] InfluxDB 连接失败: " + e.getMessage());
        }
    }

    /** 注册/更新设备 */
    public void upsertDevice(Map<String, Object> data) {
        String deviceId = (String) data.get("device_id");
        devices.put(deviceId, data);
    }

    /** 泵列表 */
    public List<Map<String, Object>> listPumps(String region, String status) {
        return new ArrayList<>(devices.values());
    }

    /** 单泵详情 */
    public Map<String, Object> getPumpDetail(String deviceId) {
        return devices.getOrDefault(deviceId, Map.of("error", "device not found"));
    }

    /** 维修历史 */
    public List<Map<String, Object>> getMaintenanceHistory(String deviceId) {
        // Demo 返回空列表，后续接入 PostgreSQL work_orders 表
        return List.of();
    }

    /** 全局统计 */
    public Map<String, Object> getGlobalStats() {
        long total = devices.size();
        long healthy = devices.values().stream()
                .filter(d -> {
                    Object hi = d.get("current_hi");
                    return hi != null && ((Number) hi).doubleValue() >= 85;
                }).count();
        long warning = devices.values().stream()
                .filter(d -> {
                    Object hi = d.get("current_hi");
                    return hi != null && ((Number) hi).doubleValue() < 70;
                }).count();

        return Map.of(
                "total_pumps", total,
                "healthy_pumps", healthy,
                "warning_pumps", warning,
                "health_rate", total > 0 ? Math.round(healthy * 100.0 / total) : 100
        );
    }
}
