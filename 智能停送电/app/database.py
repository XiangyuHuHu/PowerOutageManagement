import logging
import os
from contextlib import contextmanager

import pymysql

logger = logging.getLogger(__name__)

TARGET_CHARSET = "utf8mb4"
TARGET_COLLATION = "utf8mb4_0900_ai_ci"

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "hxy19990606"),
    "database": os.environ.get("DB_NAME", "power_control"),
    "charset": TARGET_CHARSET,
    "cursorclass": pymysql.cursors.DictCursor,
}

REAL_DEVICE_SEED = [
    ("316f", "风扇电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 10, True),
    ("332f", "风扇电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 20, True),
    ("363B", "高压风机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 30, True),
    ("363A", "高压风机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 40, True),
    ("361", "低压风机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 50, True),
    ("316", "块煤磁尾泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 60, True),
    ("332", "旋流器入料泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 70, True),
    ("713", "刮板机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 80, True),
    ("712", "刮板机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 90, True),
    ("343", "压滤机入料泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 100, True),
    ("342", "压滤机入料泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 110, True),
    ("702", "带式输送机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 120, True),
    ("701", "带式输送机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 130, True),
    ("341", "搅拌电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 140, True),
    ("348", "中高压压滤机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 150, True),
    ("347", "中高压压滤机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 160, True),
    ("351", "刮板机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 170, True),
    ("350", "刮板机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 180, True),
    ("349", "刮板机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 190, True),
    ("702L", "拉紧装置", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 200, True),
    ("701L", "拉紧装置", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 210, True),
    ("334", "高层悬尾筛", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 220, True),
    ("741", "电动葫芦", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 230, True),
    ("336Y", "油泵电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房一段", 240, True),
    ("336", "主电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 250, True),
    ("352Y", "油泵电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 260, True),
    ("XQJ", "湿式洗气机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 270, True),
    ("81DY", "配电室电源", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 280, True),
    ("352", "煤泥破碎机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 290, True),
    ("338f", "风扇电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 300, True),
    ("372", "加药装置", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 310, True),
    ("371", "加药装置", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 320, True),
    ("354", "压滤排污泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 330, True),
    ("406B", "浓缩池潜污泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 340, True),
    ("406A", "浓缩池潜污泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 350, True),
    ("353", "带式输送机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 360, True),
    ("328", "重介抽封水泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 370, True),
    ("407", "电动葫芦", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 380, True),
    ("401", "浓缩机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 390, True),
    ("356", "压滤轴封水泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 400, True),
    ("403", "底流泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 410, True),
    ("402", "底流泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 420, True),
    ("405", "冲洗水泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 430, True),
    ("711FB", "电液翻板", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 440, True),
    ("702B", "精煤采制样", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 450, True),
    ("701B", "精煤采制样", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 460, True),
    ("345", "压榨水泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 470, True),
    ("711Y", "油泵电机", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 480, True),
    ("711B", "块精煤分级筛", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房二段", 490, True),
    ("711A", "块精煤分级筛", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 500, True),
    ("713EZ", "混煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 510, True),
    ("713GZ", "混煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 520, True),
    ("713AZ", "混煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 530, True),
    ("713CZ", "混煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 540, True),
    ("712EZ", "精煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 550, True),
    ("712GZ", "精煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 560, True),
    ("712AZ", "精煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 570, True),
    ("712CZ", "精煤配仓液压站", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 580, True),
    ("338", "清水泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 590, True),
    ("YSC", "沉淀池排水泵", "主厂房660V系统图一", "31MCC-01", "main-plant-01", "主厂房三段", 600, True),
    ("128f", "风扇电机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 610, True),
    ("129f", "风扇电机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 620, True),
    ("130f", "风扇电机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 630, True),
    ("131f", "风扇电机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 640, True),
    ("132f", "风扇电机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 650, True),
    ("902", "矸石给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 660, True),
    ("903", "矸石给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 670, True),
    ("127", "带式给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 680, True),
    ("128", "带式给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 690, True),
    ("129", "带式给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 700, True),
    ("130", "带式给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 710, True),
    ("131", "带式给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 720, True),
    ("132", "带式给煤机", "主厂房660V系统图二", "31MCC-08", "main-plant-08", "主厂房二号柜", 730, True),
    ("YSC-CP", "雨水排水泵", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 740, True),
    ("721Z", "闸口液压站", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 750, True),
    ("725Z", "闸口液压站", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 760, True),
    ("729Z", "闸口液压站", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 770, True),
    ("733Z", "闸口液压站", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 780, True),
    ("743", "仓下排污泵", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 790, True),
    ("744", "仓下排污泵", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 800, True),
    ("311C-22", "进线柜311C柜-22柜", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 810, True),
    ("721f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 820, True),
    ("722f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 830, True),
    ("723f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 840, True),
    ("724f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 850, True),
    ("725f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 860, True),
    ("726f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 870, True),
    ("727f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 880, True),
    ("728f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 890, True),
    ("BYFAN", "备用风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 900, True),
    ("729f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 910, True),
    ("730f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 920, True),
    ("731f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 930, True),
    ("732f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 940, True),
    ("733f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 950, True),
    ("734f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 960, True),
    ("735f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 970, True),
    ("736f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 980, True),
    ("737f", "风扇电机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 990, True),
    ("721", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1000, True),
    ("722", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1010, True),
    ("723", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1020, True),
    ("724", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1030, True),
    ("725", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1040, True),
    ("726", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1050, True),
    ("727", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1060, True),
    ("728", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1070, True),
    ("729", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1080, True),
    ("730", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1090, True),
    ("731", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1100, True),
    ("732", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1110, True),
    ("733", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1120, True),
    ("734", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1130, True),
    ("735", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1140, True),
    ("736", "仓下给煤机", "产品仓660V系统图", "产品仓660V", "product-warehouse", "产品仓", 1150, True),
]


def get_db():
    """Return a configured database connection."""
    try:
        db = pymysql.connect(**DB_CONFIG)
        with db.cursor() as cursor:
            cursor.execute(f"SET NAMES {TARGET_CHARSET}")
            cursor.execute(f"SET CHARACTER SET {TARGET_CHARSET}")
            cursor.execute(f"SET character_set_connection={TARGET_CHARSET}")
        return db
    except Exception:
        logger.exception("数据库连接失败")
        return None


@contextmanager
def get_db_cursor():
    """Yield a database cursor with automatic commit/rollback."""
    db = get_db()
    if not db:
        raise RuntimeError("数据库连接失败")

    try:
        with db.cursor() as cursor:
            yield cursor
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def normalize_schema_collation(cursor):
    """Normalize existing schema to a single utf8mb4 collation on MySQL 8."""
    cursor.execute("SELECT DATABASE() AS db_name")
    row = cursor.fetchone() or {}
    db_name = row.get("db_name")
    if not db_name:
        return

    cursor.execute(
        """
        SELECT TABLE_NAME, TABLE_COLLATION
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s
          AND TABLE_TYPE = 'BASE TABLE'
        """,
        (db_name,),
    )
    for table in cursor.fetchall():
        table_name = table["TABLE_NAME"]
        table_collation = table.get("TABLE_COLLATION")
        if table_collation and table_collation != TARGET_COLLATION:
            cursor.execute(
                f"ALTER TABLE `{table_name}` CONVERT TO CHARACTER SET {TARGET_CHARSET} COLLATE {TARGET_COLLATION}"
            )


def ensure_applications_batch_column(cursor):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'applications'
          AND COLUMN_NAME = 'batch_id'
        """
    )
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE applications ADD COLUMN batch_id INT NULL COMMENT '大检修批次ID'")


def ensure_user_managed_devices_table(cursor):
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS user_managed_devices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            device_id VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_user_managed_device (user_id, device_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
        """
    )


def ensure_device_signal_points_table(cursor):
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS device_signal_points (
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
        ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
        """
    )


def init_database():
    """Create missing auxiliary tables, normalize collation, and seed device metadata."""
    try:
        with get_db_cursor() as cursor:
            normalize_schema_collation(cursor)

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS devices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    device_id VARCHAR(100) NOT NULL UNIQUE COMMENT '设备编号',
                    device_name VARCHAR(150) NOT NULL COMMENT '设备名称',
                    power_room VARCHAR(100) COMMENT '配电室',
                    cabinet VARCHAR(100) COMMENT '柜号',
                    area_code VARCHAR(100) COMMENT '区域编码',
                    line_name VARCHAR(100) COMMENT '线路名称',
                    sort_order INT DEFAULT 0 COMMENT '排序',
                    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
                """
            )

            cursor.executemany(
                """
                INSERT INTO devices
                (device_id, device_name, power_room, cabinet, area_code, line_name, sort_order, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    device_name = VALUES(device_name),
                    power_room = VALUES(power_room),
                    cabinet = VALUES(cabinet),
                    area_code = VALUES(area_code),
                    line_name = VALUES(line_name),
                    sort_order = VALUES(sort_order),
                    is_active = VALUES(is_active)
                """,
                REAL_DEVICE_SEED,
            )
            cursor.execute(
                """
                UPDATE devices
                SET is_active = FALSE
                WHERE device_id IN ('PDC-A1', 'PDC-A2', 'PDC-B1')
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    type ENUM('info', 'warning', 'success', 'error') DEFAULT 'info',
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS user_room_scopes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    power_room VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uniq_user_room (user_id, power_room),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS user_function_permissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    permission_code VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uniq_user_permission (user_id, permission_code),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
                """
            )

            ensure_user_managed_devices_table(cursor)
            ensure_device_signal_points_table(cursor)

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS maintenance_batches (
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
                ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
                """
            )

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS maintenance_batch_devices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    batch_id INT NOT NULL,
                    device_id VARCHAR(100) NOT NULL,
                    application_id INT NULL,
                    item_status ENUM('pending', 'generated', 'completed') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uniq_batch_device (batch_id, device_id),
                    FOREIGN KEY (batch_id) REFERENCES maintenance_batches(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
                """
            )

            ensure_applications_batch_column(cursor)

            cursor.execute(
                f"""
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
                    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET={TARGET_CHARSET} COLLATE={TARGET_COLLATION}
                """
            )

            for sql in (
                "CREATE INDEX idx_devices_room_active ON devices(power_room, is_active)",
                "CREATE INDEX idx_devices_sort_order ON devices(sort_order)",
                "CREATE INDEX idx_notifications_user_id ON notifications(user_id)",
                "CREATE INDEX idx_notifications_is_read ON notifications(is_read)",
                "CREATE INDEX idx_user_room_scopes_room ON user_room_scopes(power_room)",
                "CREATE INDEX idx_user_function_permissions_code ON user_function_permissions(permission_code)",
                "CREATE INDEX idx_user_managed_devices_device ON user_managed_devices(device_id)",
                "CREATE INDEX idx_device_signal_points_device_type ON device_signal_points(device_id, signal_type)",
                "CREATE INDEX idx_device_signal_points_address ON device_signal_points(signal_address)",
                "CREATE INDEX idx_maintenance_batches_room_status ON maintenance_batches(power_room, batch_status)",
                "CREATE INDEX idx_maintenance_batch_devices_device ON maintenance_batch_devices(device_id)",
                "CREATE INDEX idx_applications_batch_id ON applications(batch_id)",
                "CREATE INDEX idx_device_tag_records_device_status ON device_tag_records(device_id, tag_status)",
                "CREATE INDEX idx_device_tag_records_app_electrician ON device_tag_records(application_id, electrician_id)",
            ):
                try:
                    cursor.execute(sql)
                except Exception:
                    pass

        logger.info("数据库初始化完成")
        return True
    except Exception:
        logger.exception("数据库初始化失败")
        return False
