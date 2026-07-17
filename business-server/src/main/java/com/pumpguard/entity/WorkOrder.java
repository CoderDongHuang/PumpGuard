package com.pumpguard.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

/**
 * 工单实体
 *
 * 与架构说明书 3.3.1 工单自动生成与路由一致
 */
@Data
@Entity
@Table(name = "work_orders")
@NoArgsConstructor
@AllArgsConstructor
public class WorkOrder {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String id;

    @Column(name = "device_id", nullable = false)
    private String deviceId;

    @Column(name = "fault_type")
    private String faultType;          // 预测故障类型

    @Column(name = "severity", nullable = false)
    private String severity;           // P0(危险) / P1(严重) / P2(警告) / P3(关注)

    private String description;        // 故障描述 + AI 诊断结果

    @Column(name = "suggested_action")
    private String suggestedAction;    // 建议处置方案

    @Column(name = "spare_parts")
    private String spareParts;         // 所需备件（JSON 数组字符串）

    @Column(name = "assigned_engineer")
    private String assignedEngineer;   // 分配的工程师

    @Column(name = "status", nullable = false)
    private String status;             // pending / in_progress / completed / cancelled

    @Column(name = "ai_diagnosis_correct")
    private Boolean aiDiagnosisCorrect; // AI 诊断是否正确（维修反馈）

    @Column(name = "actual_fault")
    private String actualFault;        // 实际故障原因（维修反馈）

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

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
