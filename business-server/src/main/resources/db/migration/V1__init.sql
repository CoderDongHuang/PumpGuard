-- PumpGuard 数据库初始化
-- Flyway 迁移 V1

-- 1. 设备台账
CREATE TABLE IF NOT EXISTS devices (
    id              VARCHAR(36) PRIMARY KEY,
    device_id       VARCHAR(20) NOT NULL UNIQUE,
    pump_type       VARCHAR(30) NOT NULL,
    device_type     VARCHAR(10) NOT NULL DEFAULT 'smart',
    rated_flow      DOUBLE PRECISION,
    rated_head      DOUBLE PRECISION,
    rated_efficiency DOUBLE PRECISION,
    rated_power     DOUBLE PRECISION,
    rated_speed     DOUBLE PRECISION,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    country         VARCHAR(50),
    location        VARCHAR(200),
    current_hi      DOUBLE PRECISION,
    hi_grade        VARCHAR(10),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_country ON devices(country);
CREATE INDEX idx_devices_hi ON devices(current_hi);

-- 2. 工单
CREATE TABLE IF NOT EXISTS work_orders (
    id                  VARCHAR(36) PRIMARY KEY,
    device_id           VARCHAR(20) NOT NULL REFERENCES devices(device_id),
    fault_type          VARCHAR(50),
    severity            VARCHAR(5) NOT NULL DEFAULT 'P3',
    description         TEXT,
    suggested_action    TEXT,
    spare_parts         TEXT,
    assigned_engineer   VARCHAR(50),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    ai_diagnosis_correct BOOLEAN,
    actual_fault        VARCHAR(100),
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMP
);

CREATE INDEX idx_workorders_device ON work_orders(device_id);
CREATE INDEX idx_workorders_status ON work_orders(status);

-- 3. 告警事件
CREATE TABLE IF NOT EXISTS alerts (
    id              VARCHAR(36) PRIMARY KEY,
    device_id       VARCHAR(20) NOT NULL REFERENCES devices(device_id),
    fault_type      VARCHAR(50),
    health_index    DOUBLE PRECISION,
    probability     DOUBLE PRECISION,
    severity        VARCHAR(5) NOT NULL DEFAULT 'P2',
    suggested_action TEXT,
    acknowledged    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_device ON alerts(device_id);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);

-- 4. 维修反馈
CREATE TABLE IF NOT EXISTS maintenance_feedback (
    id              VARCHAR(36) PRIMARY KEY,
    work_order_id   VARCHAR(36) REFERENCES work_orders(id),
    device_id       VARCHAR(20) NOT NULL,
    ai_diagnosis    VARCHAR(200),
    actual_fault    VARCHAR(200),
    is_correct      BOOLEAN NOT NULL,
    engineer_notes  TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feedback_device ON maintenance_feedback(device_id);
