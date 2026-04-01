#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 V2.0
安全地执行数据库结构升级
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
import pymysql

def column_exists(cursor, table, column):
    """检查字段是否存在"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
    """, (table, column))
    result = cursor.fetchone()
    return result['count'] > 0

def table_exists(cursor, table):
    """检查表是否存在"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
    """, (table,))
    result = cursor.fetchone()
    return result['count'] > 0

def index_exists(cursor, table, index):
    """检查索引是否存在"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        AND INDEX_NAME = %s
    """, (table, index))
    result = cursor.fetchone()
    return result['count'] > 0

def run_migration():
    """执行迁移"""
    db = get_db()
    if not db:
        print("❌ 数据库连接失败")
        return False
    
    try:
        cursor = db.cursor(pymysql.cursors.DictCursor)
        
        print("🔄 开始数据库迁移 V2.0...")
        
        # ============================================
        # 1. 创建设备状态表
        # ============================================
        if not table_exists(cursor, 'device_status'):
            print("📋 创建 device_status 表...")
            cursor.execute("""
                CREATE TABLE device_status (
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备状态表（MQTT数据）'
            """)
            print("✅ device_status 表创建成功")
        else:
            print("ℹ️  device_status 表已存在，跳过")
        
        # ============================================
        # 2. 创建申请人表
        # ============================================
        if not table_exists(cursor, 'operation_applicants'):
            print("📋 创建 operation_applicants 表...")
            cursor.execute("""
                CREATE TABLE operation_applicants (
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作申请人表（支持多人）'
            """)
            print("✅ operation_applicants 表创建成功")
        else:
            print("ℹ️  operation_applicants 表已存在，跳过")
        
        # ============================================
        # 3. 创建操作步骤表
        # ============================================
        if not table_exists(cursor, 'operation_steps'):
            print("📋 创建 operation_steps 表...")
            cursor.execute("""
                CREATE TABLE operation_steps (
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作步骤表'
            """)
            print("✅ operation_steps 表创建成功")
        else:
            print("ℹ️  operation_steps 表已存在，跳过")
        
        # ============================================
        # 4. 创建设备状态历史表
        # ============================================
        if not table_exists(cursor, 'device_status_history'):
            print("📋 创建 device_status_history 表...")
            cursor.execute("""
                CREATE TABLE device_status_history (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    device_id VARCHAR(100) NOT NULL COMMENT '设备编号',
                    power_status ENUM('powered', 'unpowered') COMMENT '带电状态',
                    tag_status ENUM('tagged', 'untagged') COMMENT '挂牌状态',
                    electrician_name VARCHAR(100) COMMENT '电工名称',
                    status_data JSON COMMENT '完整状态数据',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '状态时间',
                    INDEX idx_device_timestamp (device_id, timestamp),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备状态历史表'
            """)
            print("✅ device_status_history 表创建成功")
        else:
            print("ℹ️  device_status_history 表已存在，跳过")
        
        # ============================================
        # 5. 修改applications表（添加新字段）
        # ============================================
        print("📋 修改 applications 表...")
        columns_to_add = [
            ('initial_power_status', "ENUM('powered', 'unpowered') COMMENT '初始带电状态（MQTT）'"),
            ('tag_status', "ENUM('tagged', 'untagged') COMMENT '挂牌状态（MQTT）'"),
            ('tag_operator', 'VARCHAR(100) COMMENT \'挂牌操作人\''),
            ('tag_time', 'TIMESTAMP NULL COMMENT \'挂牌时间\''),
            ('final_status', "ENUM('completed', 'fault') COMMENT '最终状态'"),
            ('fault_reason', 'TEXT COMMENT \'故障原因\''),
            ('current_step', 'VARCHAR(50) COMMENT \'当前步骤名称\''),
            ('operation_type', "ENUM('power_off', 'power_on') COMMENT '操作类型：停电/送电'")
        ]
        
        for column_name, column_def in columns_to_add:
            if not column_exists(cursor, 'applications', column_name):
                print(f"  ➕ 添加字段 {column_name}...")
                cursor.execute(f"ALTER TABLE applications ADD COLUMN {column_name} {column_def}")
                print(f"  ✅ 字段 {column_name} 添加成功")
            else:
                print(f"  ℹ️  字段 {column_name} 已存在，跳过")
        
        # ============================================
        # 6. 添加索引
        # ============================================
        print("📋 添加索引...")
        indexes_to_add = [
            ('applications', 'idx_operation_type', 'operation_type'),
            ('applications', 'idx_current_step', 'current_step'),
            ('applications', 'idx_final_status', 'final_status')
        ]
        
        for table, index_name, column in indexes_to_add:
            if not index_exists(cursor, table, index_name):
                print(f"  ➕ 添加索引 {table}.{index_name}...")
                cursor.execute(f"CREATE INDEX {index_name} ON {table}({column})")
                print(f"  ✅ 索引 {index_name} 添加成功")
            else:
                print(f"  ℹ️  索引 {index_name} 已存在，跳过")
        
        db.commit()
        print("\n✅ 数据库迁移 V2.0 完成！")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
