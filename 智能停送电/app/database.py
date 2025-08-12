import pymysql
import os
from contextlib import contextmanager

# 数据库配置
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'hxy19990606'),
    'database': os.environ.get('DB_NAME', 'power_control'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db():
    """获取数据库连接"""
    try:
        db = pymysql.connect(**DB_CONFIG)
        # 设置字符集
        with db.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4")
            cursor.execute("SET CHARACTER SET utf8mb4")
            cursor.execute("SET character_set_connection=utf8mb4")
        return db
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

@contextmanager
def get_db_cursor():
    """数据库游标上下文管理器"""
    db = get_db()
    if db:
        try:
            with db.cursor() as cursor:
                yield cursor
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    else:
        raise Exception("数据库连接失败")

def init_database():
    """初始化数据库表"""
    try:
        with get_db_cursor() as cursor:
            # 创建通知表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    type ENUM('info', 'warning', 'success', 'error') DEFAULT 'info',
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建索引（MySQL 8.0不支持IF NOT EXISTS）
            try:
                cursor.execute("CREATE INDEX idx_notifications_user_id ON notifications(user_id)")
            except:
                pass  # 索引已存在
            try:
                cursor.execute("CREATE INDEX idx_notifications_is_read ON notifications(is_read)")
            except:
                pass  # 索引已存在
            
        print("✅ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False 