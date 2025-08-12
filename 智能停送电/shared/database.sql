-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS power_control
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE power_control;

-- 2. 删除旧表
DROP TABLE IF EXISTS application_logs;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS users;

-- 3. 用户表
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名',
  password VARCHAR(255) NOT NULL COMMENT '密码',
  role ENUM('admin', 'dispatcher', 'electrician', 'user') NOT NULL DEFAULT 'user' COMMENT '角色',
  realname VARCHAR(100) COMMENT '真实姓名',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 停送电申请表
CREATE TABLE applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  applicant VARCHAR(100) NOT NULL COMMENT '申请人',
  applicant_id INT COMMENT '申请人用户ID',
  deviceId VARCHAR(100) NOT NULL COMMENT '设备编号',
  reason TEXT NOT NULL COMMENT '停电原因',
  operation_task TEXT COMMENT '操作任务描述',
  ticket_template VARCHAR(100) COMMENT '关联操作票模板',
  power_off_time VARCHAR(100) NOT NULL COMMENT '计划停电时间',
  power_on_time VARCHAR(100) COMMENT '计划送电时间',
  status VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '当前状态',
  -- 停电环节审批
  power_off_approver VARCHAR(100) COMMENT '停电审批人',
  power_off_approver_id INT COMMENT '停电审批人ID',
  power_off_approve_time TIMESTAMP NULL COMMENT '停电审批时间',
  power_off_approve_comment TEXT COMMENT '停电审批意见',
  -- 电工验电环节
  electrician_verifier VARCHAR(100) COMMENT '电工验电人',
  electrician_verifier_id INT COMMENT '电工验电人ID',
  electrician_verify_time TIMESTAMP NULL COMMENT '电工验电时间',
  electrician_verify_comment TEXT COMMENT '电工验电意见',
  safety_measures TEXT COMMENT '安全措施确认',
  -- 检修操作环节
  repair_operator VARCHAR(100) COMMENT '检修操作人',
  repair_operator_id INT COMMENT '检修操作人ID',
  repair_start_time TIMESTAMP NULL COMMENT '检修开始时间',
  repair_end_time TIMESTAMP NULL COMMENT '检修结束时间',
  repair_comment TEXT COMMENT '检修操作说明',
  -- 送电环节审批
  power_on_applicant VARCHAR(100) COMMENT '送电申请人',
  power_on_applicant_id INT COMMENT '送电申请人ID',
  power_on_apply_time TIMESTAMP NULL COMMENT '送电申请时间',
  power_on_approver VARCHAR(100) COMMENT '送电审批人',
  power_on_approver_id INT COMMENT '送电审批人ID',
  power_on_approve_time TIMESTAMP NULL COMMENT '送电审批时间',
  power_on_approve_comment TEXT COMMENT '送电审批意见',
  -- 完成信息
  completed_time TIMESTAMP NULL COMMENT '完成时间',
  total_duration INT COMMENT '总耗时(分钟)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. 操作日志表
CREATE TABLE application_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT NOT NULL COMMENT '关联申请ID',
  operator VARCHAR(100) NOT NULL COMMENT '操作人',
  operator_id INT NOT NULL COMMENT '操作人ID',
  operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
  operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  operation_comment TEXT COMMENT '操作说明',
  old_status VARCHAR(50) COMMENT '操作前状态',
  new_status VARCHAR(50) COMMENT '操作后状态',
  FOREIGN KEY (application_id) REFERENCES applications(id)
);

-- 6. 默认用户数据
INSERT IGNORE INTO users (username, password, role, realname) VALUES
('admin', 'admin', 'admin', '管理员'),
('dispatcher1', '123456', 'dispatcher', '调度员张三'),
('electrician1', '123456', 'electrician', '电工李四'),
('user1', '123456', 'user', '普通用户A');

-- 创建通知表
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    type ENUM('info', 'warning', 'success', 'error') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 添加索引优化查询性能
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_applicant_id ON applications(applicant_id);
CREATE INDEX idx_applications_created_at ON applications(created_at);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);