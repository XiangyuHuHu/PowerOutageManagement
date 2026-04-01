-- 1. 创建数据�?CREATE DATABASE IF NOT EXISTS power_control
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE power_control;

-- 2. 删除旧表
DROP TABLE IF EXISTS application_logs;
DROP TABLE IF EXISTS device_tag_records;
DROP TABLE IF EXISTS maintenance_batch_devices;
DROP TABLE IF EXISTS maintenance_batches;
DROP TABLE IF EXISTS user_managed_devices;
DROP TABLE IF EXISTS device_signal_points;
DROP TABLE IF EXISTS user_function_permissions;
DROP TABLE IF EXISTS user_room_scopes;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS users;

-- 3. 用户�?CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE COMMENT '用户�?,
  password VARCHAR(255) NOT NULL COMMENT '密码',
  role ENUM('admin', 'dispatcher', 'electrician', 'user') NOT NULL DEFAULT 'user' COMMENT '角色',
  realname VARCHAR(100) COMMENT '真实姓名',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 停送电申请�?CREATE TABLE devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(100) NOT NULL UNIQUE COMMENT '设备编号',
  device_name VARCHAR(150) NOT NULL COMMENT '设备名称',
  power_room VARCHAR(100) COMMENT '配电�?,
  cabinet VARCHAR(100) COMMENT '柜号',
  area_code VARCHAR(100) COMMENT '区域编码',
  line_name VARCHAR(100) COMMENT '线路名称',
  sort_order INT DEFAULT 0 COMMENT '排序',
  is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO devices (device_id, device_name, power_room, cabinet, area_code, line_name, sort_order, is_active) VALUES
('316f', '风扇电机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 10, TRUE),
('332f', '风扇电机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 20, TRUE),
('363B', '高压风机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 30, TRUE),
('363A', '高压风机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 40, TRUE),
('361', '低压风机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 50, TRUE),
('316', '块煤磁尾泵', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 60, TRUE),
('332', '旋流器入料泵', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 70, TRUE),
('713', '刮板机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 80, TRUE),
('712', '刮板机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 90, TRUE),
('343', '压滤机入料泵', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 100, TRUE),
('342', '压滤机入料泵', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 110, TRUE),
('702', '带式输送机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 120, TRUE),
('701', '带式输送机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 130, TRUE),
('341', '搅拌电机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 140, TRUE),
('348', '中高压压滤机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 150, TRUE),
('347', '中高压压滤机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 160, TRUE),
('351', '刮板机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 170, TRUE),
('350', '刮板机', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房一段', 180, TRUE),
('711A', '块精煤分级筛', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房三段', 190, TRUE),
('338', '清水泵', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房三段', 200, TRUE),
('YSC', '沉淀池排水泵', '主厂房660V系统图一', '31MCC-01', 'main-plant-01', '主厂房三段', 210, TRUE),
('128f', '风扇电机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 220, TRUE),
('129f', '风扇电机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 230, TRUE),
('130f', '风扇电机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 240, TRUE),
('131f', '风扇电机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 250, TRUE),
('132f', '风扇电机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 260, TRUE),
('902', '矸石给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 270, TRUE),
('903', '矸石给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 280, TRUE),
('127', '带式给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 290, TRUE),
('128', '带式给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 300, TRUE),
('129', '带式给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 310, TRUE),
('130', '带式给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 320, TRUE),
('131', '带式给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 330, TRUE),
('132', '带式给煤机', '主厂房660V系统图二', '31MCC-08', 'main-plant-08', '主厂房二号柜', 340, TRUE),
('YSC-CP', '雨水排水泵', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 350, TRUE),
('721Z', '闸口液压站', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 360, TRUE),
('725Z', '闸口液压站', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 370, TRUE),
('729Z', '闸口液压站', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 380, TRUE),
('733Z', '闸口液压站', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 390, TRUE),
('743', '仓下排污泵', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 400, TRUE),
('744', '仓下排污泵', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 410, TRUE),
('311C-22', '进线柜311C柜-22柜', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 420, TRUE),
('721f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 430, TRUE),
('722f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 440, TRUE),
('723f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 450, TRUE),
('724f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 460, TRUE),
('725f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 470, TRUE),
('726f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 480, TRUE),
('727f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 490, TRUE),
('728f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 500, TRUE),
('729f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 510, TRUE),
('730f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 520, TRUE),
('731f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 530, TRUE),
('732f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 540, TRUE),
('733f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 550, TRUE),
('734f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 560, TRUE),
('735f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 570, TRUE),
('736f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 580, TRUE),
('737f', '风扇电机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 590, TRUE),
('721', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 600, TRUE),
('722', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 610, TRUE),
('723', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 620, TRUE),
('724', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 630, TRUE),
('725', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 640, TRUE),
('726', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 650, TRUE),
('727', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 660, TRUE),
('728', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 670, TRUE),
('729', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 680, TRUE),
('730', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 690, TRUE),
('731', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 700, TRUE),
('732', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 710, TRUE),
('733', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 720, TRUE),
('734', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 730, TRUE),
('735', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 740, TRUE),
('736', '仓下给煤机', '产品仓660V系统图', '产品仓660V', 'product-warehouse', '产品仓', 750, TRUE);

-- 5. 停送电申请�?CREATE TABLE applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  applicant VARCHAR(100) NOT NULL COMMENT '申请�?,
  applicant_id INT COMMENT '申请人用户ID',
  deviceId VARCHAR(100) NOT NULL COMMENT '设备编号',
  reason TEXT NOT NULL COMMENT '停电原因',
  operation_task TEXT COMMENT '操作任务描述',
  ticket_template VARCHAR(100) COMMENT '关联操作票模�?,
  power_off_time VARCHAR(100) NOT NULL COMMENT '计划停电时间',
  power_on_time VARCHAR(100) COMMENT '计划送电时间',
  status VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT '当前状�?,
  -- 停电环节审批
  power_off_approver VARCHAR(100) COMMENT '停电审批�?,
  power_off_approver_id INT COMMENT '停电审批人ID',
  power_off_approve_time TIMESTAMP NULL COMMENT '停电审批时间',
  power_off_approve_comment TEXT COMMENT '停电审批意见',
  -- 电工验电环节
  electrician_verifier VARCHAR(100) COMMENT '电工验电�?,
  electrician_verifier_id INT COMMENT '电工验电人ID',
  electrician_verify_time TIMESTAMP NULL COMMENT '电工验电时间',
  electrician_verify_comment TEXT COMMENT '电工验电意见',
  safety_measures TEXT COMMENT '安全措施确认',
  -- 检修操作环�?  repair_operator VARCHAR(100) COMMENT '检修操作人',
  repair_operator_id INT COMMENT '检修操作人ID',
  repair_start_time TIMESTAMP NULL COMMENT '检修开始时�?,
  repair_end_time TIMESTAMP NULL COMMENT '检修结束时�?,
  repair_comment TEXT COMMENT '检修操作说�?,
  -- 送电环节审批
  power_on_applicant VARCHAR(100) COMMENT '送电申请�?,
  power_on_applicant_id INT COMMENT '送电申请人ID',
  power_on_apply_time TIMESTAMP NULL COMMENT '送电申请时间',
  power_on_approver VARCHAR(100) COMMENT '送电审批�?,
  power_on_approver_id INT COMMENT '送电审批人ID',
  power_on_approve_time TIMESTAMP NULL COMMENT '送电审批时间',
  power_on_approve_comment TEXT COMMENT '送电审批意见',
  batch_id INT NULL COMMENT '大检修批次ID',
  -- 完成信息
  completed_time TIMESTAMP NULL COMMENT '完成时间',
  total_duration INT COMMENT '总耗时(分钟)',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 6. 操作日志�?CREATE TABLE application_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT NOT NULL COMMENT '关联申请ID',
  operator VARCHAR(100) NOT NULL COMMENT '操作�?,
  operator_id INT NOT NULL COMMENT '操作人ID',
  operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
  operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  operation_comment TEXT COMMENT '操作说明',
  old_status VARCHAR(50) COMMENT '操作前状�?,
  new_status VARCHAR(50) COMMENT '操作后状�?,
  FOREIGN KEY (application_id) REFERENCES applications(id)
);

-- 7. 挂牌记录表（支持多人挂牌、本人解本人牌）
CREATE TABLE device_tag_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(100) NOT NULL COMMENT '设备编号',
  application_id INT NOT NULL COMMENT '关联申请ID',
  electrician_id INT NOT NULL COMMENT '挂牌电工ID',
  electrician_name VARCHAR(100) NOT NULL COMMENT '挂牌电工姓名',
  tag_status ENUM('active', 'released') DEFAULT 'active' COMMENT '挂牌状�?,
  tag_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '挂牌时间',
  release_time TIMESTAMP NULL COMMENT '解牌时间',
  release_application_id INT NULL COMMENT '解牌关联工单ID',
  release_operator_id INT NULL COMMENT '解牌操作人ID',
  release_operator_name VARCHAR(100) NULL COMMENT '解牌操作人姓�?,
  release_comment TEXT COMMENT '解牌说明',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- 8. 默认用户数据（上线前务必修改密码�?INSERT IGNORE INTO users (username, password, role, realname) VALUES
('admin', 'ChangeMe_Admin_2026!', 'admin', '管理�?),
('dispatcher1', 'ChangeMe_Dispatcher_2026!', 'dispatcher', '调度员张�?),
('electrician1', 'ChangeMe_Electrician_2026!', 'electrician', '电工李四'),
('user1', 'ChangeMe_User_2026!', 'user', '普通用户A');

-- 9. 创建通知�?CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    type ENUM('info', 'warning', 'success', 'error') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_room_scopes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  power_room VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_user_room (user_id, power_room),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_function_permissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  permission_code VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_user_permission (user_id, permission_code),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_managed_devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  device_id VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_user_managed_device (user_id, device_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE device_signal_points (
  id INT AUTO_INCREMENT PRIMARY KEY,
  device_id VARCHAR(100) NOT NULL,
  signal_type VARCHAR(64) NOT NULL,
  signal_name VARCHAR(255) NOT NULL,
  signal_address VARCHAR(128),
  data_type VARCHAR(64) DEFAULT 'bool',
  source_system VARCHAR(64) DEFAULT 'plc',
  source_sheet VARCHAR(64),
  description VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_device_signal (device_id, signal_type, signal_name)
);

INSERT INTO user_function_permissions (user_id, permission_code)
SELECT id, 'approval_center' FROM users WHERE role = 'admin'
UNION ALL
SELECT id, 'batch_approval' FROM users WHERE role = 'admin'
UNION ALL
SELECT id, 'device_monitor' FROM users WHERE role = 'admin'
UNION ALL
SELECT id, 'notifications' FROM users WHERE role = 'admin'
UNION ALL
SELECT id, 'stats' FROM users WHERE role = 'admin'
UNION ALL
SELECT id, 'user_management' FROM users WHERE role = 'admin'
UNION ALL
SELECT id, 'approval_center' FROM users WHERE role = 'dispatcher'
UNION ALL
SELECT id, 'batch_approval' FROM users WHERE role = 'dispatcher'
UNION ALL
SELECT id, 'device_monitor' FROM users WHERE role = 'dispatcher'
UNION ALL
SELECT id, 'notifications' FROM users WHERE role = 'dispatcher'
UNION ALL
SELECT id, 'apply' FROM users WHERE role = 'electrician'
UNION ALL
SELECT id, 'repair' FROM users WHERE role = 'electrician'
UNION ALL
SELECT id, 'power_on_apply' FROM users WHERE role = 'electrician'
UNION ALL
SELECT id, 'device_monitor' FROM users WHERE role = 'electrician'
UNION ALL
SELECT id, 'notifications' FROM users WHERE role = 'electrician'
UNION ALL
SELECT id, 'batch_management' FROM users WHERE role = 'admin'
UNION ALL
SELECT id, 'apply' FROM users WHERE role = 'user';

CREATE TABLE maintenance_batches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  batch_name VARCHAR(150) NOT NULL,
  power_room VARCHAR(100) NOT NULL,
  batch_status ENUM('draft', 'generated', 'in_progress', 'completed') DEFAULT 'draft',
  description TEXT,
  planned_start_time VARCHAR(100),
  planned_end_time VARCHAR(100),
  created_by_id INT,
  created_by_name VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE maintenance_batch_devices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  batch_id INT NOT NULL,
  device_id VARCHAR(100) NOT NULL,
  application_id INT NULL,
  item_status ENUM('pending', 'generated', 'completed') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_batch_device (batch_id, device_id),
  FOREIGN KEY (batch_id) REFERENCES maintenance_batches(id) ON DELETE CASCADE
);

-- 添加索引优化查询性能
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_applicant_id ON applications(applicant_id);
CREATE INDEX idx_applications_created_at ON applications(created_at);
CREATE INDEX idx_applications_batch_id ON applications(batch_id);
CREATE INDEX idx_devices_room_active ON devices(power_room, is_active);
CREATE INDEX idx_devices_sort_order ON devices(sort_order);
CREATE INDEX idx_maintenance_batches_room_status ON maintenance_batches(power_room, batch_status);
CREATE INDEX idx_maintenance_batch_devices_device ON maintenance_batch_devices(device_id);
CREATE INDEX idx_device_tag_records_device_status ON device_tag_records(device_id, tag_status);
CREATE INDEX idx_device_tag_records_app_electrician ON device_tag_records(application_id, electrician_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_user_room_scopes_room ON user_room_scopes(power_room);
CREATE INDEX idx_user_function_permissions_code ON user_function_permissions(permission_code);
CREATE INDEX idx_user_managed_devices_device ON user_managed_devices(device_id);
