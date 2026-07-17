package com.pumpguard;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * PumpGuard 业务主脑 — Spring Boot 入口
 *
 * 架构定位（来自架构说明书 4.1）：
 *   Java Spring Boot = 业务骨架
 *   负责：设备管理、数据接入路由、工单流转、权限管理、告警路由、飞书 API 集成
 */
@SpringBootApplication
@EnableKafka
@EnableScheduling
public class PumpGuardApplication {

    public static void main(String[] args) {
        SpringApplication.run(PumpGuardApplication.class, args);
    }
}
