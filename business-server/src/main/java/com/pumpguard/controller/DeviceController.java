package com.pumpguard.controller;

import com.pumpguard.service.AIClientService;
import com.pumpguard.service.DeviceService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 设备管理 REST API
 *
 * 与架构说明书 Phase 5 数据 API 列表一致
 */
@RestController
@RequestMapping("/api")
public class DeviceController {

    private final DeviceService deviceService;
    private final AIClientService aiClient;

    public DeviceController(DeviceService deviceService, AIClientService aiClient) {
        this.deviceService = deviceService;
        this.aiClient = aiClient;
    }

    /** GET /api/pumps — 泵列表 */
    @GetMapping("/pumps")
    public List<Map<String, Object>> listPumps(
            @RequestParam(required = false) String region,
            @RequestParam(required = false) String status) {
        return deviceService.listPumps(region, status);
    }

    /** GET /api/pumps/{id} — 单泵详情 */
    @GetMapping("/pumps/{id}")
    public Map<String, Object> getPump(@PathVariable String id) {
        return deviceService.getPumpDetail(id);
    }

    /** GET /api/pumps/{id}/history — 单泵维修历史 */
    @GetMapping("/pumps/{id}/history")
    public List<Map<String, Object>> getPumpHistory(@PathVariable String id) {
        return deviceService.getMaintenanceHistory(id);
    }

    /** POST /api/pumps/{id}/hi — 触发 HI 计算 */
    @PostMapping("/pumps/{id}/hi")
    public Map<String, Object> computeHI(@PathVariable String id, @RequestBody Map<String, Object> request) {
        request.put("device_id", id);
        return aiClient.computeHI(request);
    }

    /** POST /api/pumps/{id}/fault — 触发故障预测 */
    @PostMapping("/pumps/{id}/fault")
    public Map<String, Object> predictFault(@PathVariable String id, @RequestBody Map<String, Object> request) {
        request.put("device_id", id);
        return aiClient.predictFault(request);
    }

    /** POST /api/pumps/{id}/rul — 触发 RUL 预测 */
    @PostMapping("/pumps/{id}/rul")
    public Map<String, Object> predictRUL(@PathVariable String id, @RequestBody Map<String, Object> request) {
        request.put("device_id", id);
        return aiClient.predictRUL(request);
    }

    /** POST /api/pumps/{id}/rca — 触发根因分析 */
    @PostMapping("/pumps/{id}/rca")
    public Map<String, Object> analyzeRCA(@PathVariable String id, @RequestBody Map<String, Object> request) {
        request.put("device_id", id);
        return aiClient.analyzeRootCause(request);
    }

    /** GET /api/stats/global — 全局统计 */
    @GetMapping("/stats/global")
    public Map<String, Object> globalStats() {
        return deviceService.getGlobalStats();
    }
}
