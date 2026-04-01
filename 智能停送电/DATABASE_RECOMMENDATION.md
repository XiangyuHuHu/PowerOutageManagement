# 数据库选型建议 - 选煤厂停送电审批系统

## 📊 当前架构分析

### 现有技术栈
- **后端**: Flask (Python)
- **数据库**: MySQL 8.0 (PyMySQL)
- **消息队列**: MQTT (paho-mqtt)
- **数据源**: KepServer → MQTT → Flask应用
- **部署**: Docker Compose

### 当前数据流
```
KepServer → MQTT Broker → Flask MQTT Client → 内存存储(DEVICE_STATUS字典)
                                                      ↓
                                              MySQL数据库(审批流程数据)
```

## 🎯 建议：继续使用 MySQL

### ✅ 推荐理由

1. **已集成完成**
   - 所有审批流程已基于MySQL实现
   - Docker配置已就绪
   - 迁移成本为零

2. **适合企业内网场景**
   - 选煤厂内部应用，无需公网访问
   - MySQL性能完全满足需求
   - 运维简单，团队熟悉度高

3. **数据特性匹配**
   - 审批流程 = 关系型数据（用户、申请、日志）
   - 设备状态 = 时序数据（可优化存储）
   - MySQL完全胜任

4. **成本效益**
   - 无需额外服务
   - 资源占用小
   - 维护成本低

### ❌ 不推荐 Supabase 的原因

1. **过度设计**
   - Supabase的实时订阅、GraphQL等功能对审批流程是多余的
   - 增加系统复杂度

2. **迁移成本高**
   - 需要重构所有数据库操作
   - 需要学习PostgreSQL语法差异
   - 需要重新配置认证系统

3. **依赖外部服务**
   - 增加网络依赖
   - 企业内网可能无法访问
   - 增加故障点

## 🔧 需要改进的地方

### ⚠️ 当前问题

**MQTT设备状态只存在内存中，未持久化到数据库**

```python
# 当前实现 (app/mqtt_client.py)
DEVICE_STATUS = {}  # 内存字典
DEVICE_HISTORY = []  # 内存列表
```

**问题**:
- 服务重启后数据丢失
- 无法查询历史状态
- 无法关联设备状态与审批记录
- 无法做统计分析

### ✅ 改进方案

#### 1. 创建设备状态表

```sql
-- 设备表
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL UNIQUE COMMENT '设备编号',
    device_name VARCHAR(200) COMMENT '设备名称',
    device_type VARCHAR(50) COMMENT '设备类型',
    location VARCHAR(200) COMMENT '设备位置',
    status VARCHAR(50) DEFAULT 'unknown' COMMENT '当前状态',
    last_update TIMESTAMP NULL COMMENT '最后更新时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 设备状态历史表（时序数据）
CREATE TABLE IF NOT EXISTS device_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL COMMENT '设备编号',
    status VARCHAR(50) NOT NULL COMMENT '设备状态',
    status_data JSON COMMENT '完整状态数据(JSON格式)',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '状态时间',
    INDEX idx_device_timestamp (device_id, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 设备告警表
CREATE TABLE IF NOT EXISTS device_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL COMMENT '设备编号',
    alert_type VARCHAR(50) NOT NULL COMMENT '告警类型',
    alert_message TEXT COMMENT '告警信息',
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_is_resolved (is_resolved),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 2. 修改MQTT客户端，持久化设备状态

```python
# app/mqtt_client.py 改进
from app.database import get_db
import pymysql

def process_device_message(data):
    """处理设备状态消息并持久化"""
    try:
        device_id = data.get('device_id', data.get('deviceId', 'unknown'))
        status = data.get('status', 'unknown')
        timestamp = data.get('timestamp', time.time())
        
        # 更新内存状态（保持实时性）
        DEVICE_STATUS[device_id] = {
            'status': status,
            'last_update': timestamp,
            'data': data
        }
        
        # 持久化到数据库
        db = get_db()
        if db:
            try:
                with db.cursor(pymysql.cursors.DictCursor) as cursor:
                    # 更新或插入设备表
                    cursor.execute("""
                        INSERT INTO devices (device_id, status, last_update)
                        VALUES (%s, %s, FROM_UNIXTIME(%s))
                        ON DUPLICATE KEY UPDATE
                            status = VALUES(status),
                            last_update = VALUES(last_update),
                            updated_at = NOW()
                    """, (device_id, status, timestamp))
                    
                    # 插入历史记录（只保存重要状态变化）
                    if should_save_history(status):
                        cursor.execute("""
                            INSERT INTO device_status_history 
                            (device_id, status, status_data, timestamp)
                            VALUES (%s, %s, %s, FROM_UNIXTIME(%s))
                        """, (device_id, status, json.dumps(data), timestamp))
                    
                    # 检查告警
                    if status in ['error', 'offline', 'overload', 'temperature_high', 'voltage_high', 'voltage_low']:
                        cursor.execute("""
                            INSERT INTO device_alerts 
                            (device_id, alert_type, alert_message, severity)
                            VALUES (%s, %s, %s, %s)
                        """, (device_id, status, get_alert_message(status), get_severity(status)))
                    
                    db.commit()
            except Exception as e:
                print(f"数据库持久化失败: {e}")
                db.rollback()
            finally:
                db.close()
        
        print(f"📊 设备状态更新: {device_id} -> {status}")
        
    except Exception as e:
        print(f"处理设备消息失败: {e}")

def should_save_history(status):
    """判断是否需要保存历史记录（避免数据过多）"""
    # 只保存重要状态变化
    important_statuses = ['error', 'offline', 'online', 'overload']
    return status in important_statuses
```

#### 3. 关联设备状态与审批记录

```sql
-- 在applications表中添加设备状态关联
ALTER TABLE applications 
ADD COLUMN device_status_at_apply VARCHAR(50) COMMENT '申请时的设备状态',
ADD COLUMN device_status_at_complete VARCHAR(50) COMMENT '完成时的设备状态';

-- 查询时可以关联设备状态
SELECT 
    a.*,
    d.status as current_device_status,
    d.last_update as device_last_update
FROM applications a
LEFT JOIN devices d ON a.deviceId = d.device_id
WHERE a.status = 'pending';
```

## 📈 性能优化建议

### 1. 设备状态历史数据归档
```sql
-- 定期归档旧数据（保留最近3个月）
DELETE FROM device_status_history 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 3 MONTH);
```

### 2. 添加Redis缓存（可选）
```python
# 对于频繁查询的设备状态，使用Redis缓存
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_device_status_cached(device_id):
    cache_key = f"device_status:{device_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 从数据库查询
    db = get_db()
    # ... 查询逻辑
    
    # 缓存5分钟
    redis_client.setex(cache_key, 300, json.dumps(status))
    return status
```

## 🚀 实施步骤

1. **第一步**: 执行SQL脚本，创建设备相关表
2. **第二步**: 修改`app/mqtt_client.py`，添加数据库持久化逻辑
3. **第三步**: 修改API接口，从数据库查询设备状态
4. **第四步**: 测试MQTT消息接收和持久化
5. **第五步**: 添加设备状态查询和统计功能

## 📝 总结

**推荐方案**: **继续使用 MySQL + 完善设备状态持久化**

- ✅ 保持现有架构，零迁移成本
- ✅ 满足所有业务需求
- ✅ 性能完全够用
- ✅ 运维简单可靠
- ✅ 只需添加设备状态表和改进MQTT处理逻辑

**不推荐 Supabase**:
- ❌ 过度设计，增加复杂度
- ❌ 迁移成本高
- ❌ 不适合企业内网场景
















