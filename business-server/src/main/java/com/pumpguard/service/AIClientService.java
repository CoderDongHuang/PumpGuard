package com.pumpguard.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;

/**
 * AI 引擎调用客户端
 *
 * 通过 HTTP REST 调用 Python FastAPI AI 引擎
 * 与架构说明书 4.2 微服务通信一致（Demo 阶段用 REST，后续切 gRPC）
 */
@Service
public class AIClientService {

    @Value("${ai-engine.url}")
    private String aiEngineUrl;

    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();

    /**
     * 调用 HI 计算
     */
    public Map<String, Object> computeHI(Map<String, Object> request) {
        return post("/api/v1/hi/compute", request);
    }

    /**
     * 调用故障预测
     */
    public Map<String, Object> predictFault(Map<String, Object> request) {
        return post("/api/v1/fault/predict", request);
    }

    /**
     * 调用 RUL 预测
     */
    public Map<String, Object> predictRUL(Map<String, Object> request) {
        return post("/api/v1/rul/predict", request);
    }

    /**
     * 调用根因分析
     */
    public Map<String, Object> analyzeRootCause(Map<String, Object> request) {
        return post("/api/v1/rca/analyze", request);
    }

    /**
     * 提交维修反馈（触发模型更新）
     */
    public Map<String, Object> submitFeedback(Map<String, Object> request) {
        return post("/api/v1/model/update", request);
    }

    private Map<String, Object> post(String path, Map<String, Object> body) {
        try {
            String json = mapper.writeValueAsString(body);
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(aiEngineUrl + path))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(json))
                    .build();
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            return mapper.readValue(response.body(), Map.class);
        } catch (Exception e) {
            throw new RuntimeException("AI Engine 调用失败: " + e.getMessage(), e);
        }
    }
}
