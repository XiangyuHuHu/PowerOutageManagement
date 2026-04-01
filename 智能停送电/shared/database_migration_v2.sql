-- ============================================
-- 数据库迁移脚本 V2.0
-- 新需求：支持多人申请、步骤管理、MQTT集成
-- ============================================

USE power_control;

-- ============================================
-- 1. 设备状态表（MQTT数据存储）
-- ============================================
CREATE TABLE IF NOT EXISTS device_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL UNIQUE COMMENT '设备编号',
    power_status ENUM('powered', 'unpowered') COMMENT '带电状态（MQTT）',
    tag_status ENUM('tagged', 'untagged') COMMENT '挂牌状态（MQTT）',
    electrician_name VARCHAR(100) COMMENT '电工名称（MQTT）',
    status_data JSON COMMENT '完整MQTT数据',
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    INDEX idx_device_id (device_id),
    INDEX idx_power_status (power_status),
    INDEX idx_tag_status (tag_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备状态表（MQTT数据）';

-- ============================================
-- 2. 申请人表（支持多人申请）
-- ============================================
CREATE TABLE IF NOT EXISTS operation_applicants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_id INT NOT NULL COMMENT '关联操作ID',
    applicant_name VARCHAR(100) NOT NULL COMMENT '申请人姓名',
    applicant_id INT COMMENT '申请人用户ID',
    applicant_role VARCHAR(50) COMMENT '申请人角色',
    is_primary BOOLEAN DEFAULT FALSE COMMENT '是否主申请人',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (operation_id) REFERENCES applications(id) ON DELETE CASCADE,
    INDEX idx_operation_id (operation_id),
    INDEX idx_applicant_id (applicant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作申请人表（支持多人）';

-- ============================================
-- 3. 操作步骤表（详细记录每个步骤）
-- ============================================
CREATE TABLE IF NOT EXISTS operation_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_id INT NOT NULL COMMENT '关联操作ID',
    step_name VARCHAR(50) NOT NULL COMMENT '步骤名称',
    step_order INT NOT NULL COMMENT '步骤顺序',
    operator_name VARCHAR(100) COMMENT '操作人姓名',
    operator_id INT COMMENT '操作人ID',
    operator_role VARCHAR(50) COMMENT '操作人角色',
    step_status ENUM('pending', 'in_progress', 'completed', 'skipped') DEFAULT 'pending' COMMENT '步骤状态',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    complete_time TIMESTAMP NULL COMMENT '完成时间',
    comment TEXT COMMENT '操作说明',
    mqtt_snapshot JSON COMMENT '步骤执行时的MQTT状态快照',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (operation_id) REFERENCES applications(id) ON DELETE CASCADE,
    INDEX idx_operation_step (operation_id, step_order),
    INDEX idx_step_status (step_status),
    INDEX idx_step_name (step_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作步骤表';

-- ============================================
-- 3.1 挂牌记录表（支持多人挂牌、本人解本人牌）
-- ============================================
CREATE TABLE IF NOT EXISTS device_tag_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL COMMENT '设备编号',
    application_id INT NOT NULL COMMENT '关联工单ID',
    electrician_id INT NOT NULL COMMENT '挂牌电工ID',
    electrician_name VARCHAR(100) NOT NULL COMMENT '挂牌电工姓名',
    tag_status ENUM('active', 'released') DEFAULT 'active' COMMENT '挂牌状态',
    tag_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '挂牌时间',
    release_time TIMESTAMP NULL COMMENT '解牌时间',
    release_application_id INT NULL COMMENT '解牌关联工单ID',
    release_operator_id INT NULL COMMENT '解牌操作人ID',
    release_operator_name VARCHAR(100) NULL COMMENT '解牌操作人姓名',
    release_comment TEXT COMMENT '解牌说明',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    INDEX idx_device_tag_records_device_status (device_id, tag_status),
    INDEX idx_device_tag_records_app_electrician (application_id, electrician_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='挂牌记录表';

-- ============================================
-- 4. 修改applications表（添加新字段）
-- ============================================

-- 添加MQTT相关字段
ALTER TABLE applications 
ADD COLUMN IF NOT EXISTS initial_power_status ENUM('powered', 'unpowered') COMMENT '初始带电状态（MQTT）',
ADD COLUMN IF NOT EXISTS tag_status ENUM('tagged', 'untagged') COMMENT '挂牌状态（MQTT）',
ADD COLUMN IF NOT EXISTS tag_operator VARCHAR(100) COMMENT '挂牌操作人',
ADD COLUMN IF NOT EXISTS tag_time TIMESTAMP NULL COMMENT '挂牌时间',
ADD COLUMN IF NOT EXISTS final_status ENUM('completed', 'fault') COMMENT '最终状态',
ADD COLUMN IF NOT EXISTS fault_reason TEXT COMMENT '故障原因',
ADD COLUMN IF NOT EXISTS current_step VARCHAR(50) COMMENT '当前步骤名称',
ADD COLUMN IF NOT EXISTS operation_type ENUM('power_off', 'power_on') COMMENT '操作类型：停电/送电';

-- 注意：MySQL 8.0.19以下不支持ADD COLUMN IF NOT EXISTS，需要使用以下方式：
-- 先检查字段是否存在，如果不存在则添加
-- 这里提供兼容脚本（需要手动执行或使用存储过程）

-- 为operation_type添加索引
CREATE INDEX IF NOT EXISTS idx_operation_type ON applications(operation_type);
CREATE INDEX IF NOT EXISTS idx_current_step ON applications(current_step);
CREATE INDEX IF NOT EXISTS idx_final_status ON applications(final_status);

-- ============================================
-- 5. 设备状态历史表（可选，用于历史查询）
-- ============================================
CREATE TABLE IF NOT EXISTS device_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL COMMENT '设备编号',
    power_status ENUM('powered', 'unpowered') COMMENT '带电状态',
    tag_status ENUM('tagged', 'untagged') COMMENT '挂牌状态',
    electrician_name VARCHAR(100) COMMENT '电工名称',
    status_data JSON COMMENT '完整状态数据',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '状态时间',
    INDEX idx_device_timestamp (device_id, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备状态历史表';

-- ============================================
-- 6. 添加步骤名称枚举参考（用于前端显示）
-- ============================================

-- 停电流程步骤：
-- 'applied' - 申请
-- 'pending_approval' - 待审批
-- 'approved' - 审批通过
-- 'power_off_operating' - 操作停电（不在程序中）
-- 'verifying' - 验电
-- 'confirmed_power_off' - 电工确认停电
-- 'tagging' - 挂牌
-- 'completed' - 完成
-- 'fault' - 报故障

-- 送电流程步骤：
-- 'power_on_applied' - 送电申请
-- 'checking_tag' - 确认挂牌状态
-- 'pending_approval' - 待审批（未挂牌时）
-- 'approved' - 审批通过
-- 'power_on_operating' - 电工送电
-- 'confirmed_power_on' - 电工确认
-- 'completed' - 完成

-- ============================================
-- 7. 数据迁移（可选，如果需要保留旧数据）
-- ============================================

-- 将现有的applications表中的申请人迁移到operation_applicants表
-- INSERT INTO operation_applicants (operation_id, applicant_name, applicant_id, is_primary)
-- SELECT id, applicant, applicant_id, TRUE
-- FROM applications
-- WHERE applicant IS NOT NULL AND applicant_id IS NOT NULL;

-- ============================================
-- 完成
-- ============================================
