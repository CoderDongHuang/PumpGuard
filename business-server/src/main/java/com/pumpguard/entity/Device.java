package com.pumpguard.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

/**
 * 设备台账实体
 *
 * 与架构说明书 3.1.4 统一数据模型对应
 */
@Data
@Entity
@Table(name = "devices")
@NoArgsConstructor
@AllArgsConstructor
public class Device {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(name = "device_id", unique = true, nullable = false)
    private String deviceId;          // 如 PUMP-0001

    @Column(name = "pump_type", nullable = false)
    private String pumpType;          // centrifugal_small / axial_flow / mixed_flow

    @Column(name = "device_type", nullable = false)
    private String deviceType;        // smart / vfd / legacy

    @Column(name = "rated_flow")
    private Double ratedFlow;         // m³/h

    @Column(name = "rated_head")
    private Double ratedHead;         // m

    @Column(name = "rated_efficiency")
    private Double ratedEfficiency;   // 0-1

    @Column(name = "rated_power")
    private Double ratedPower;        // kW

    @Column(name = "rated_speed")
    private Double ratedSpeed;        // RPM

    private Double latitude;
    private Double longitude;
    private String country;
    private String location;           // 详细位置描述

    @Column(name = "current_hi")
    private Double currentHi;          // 最新健康指数 0-100

    @Column(name = "hi_grade")
    private String hiGrade;            // 健康/关注/警告/严重/危险

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
