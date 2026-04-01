# 实时设备状态存储架构方案

## 🎯 问题分析

**需求场景**：
- 设备带电状态需要**实时显示**（前端每30秒轮询）
- MQTT持续推送设备状态更新
- 需要查询历史状态记录

**性能考虑**：
- 实时查询要求**低延迟**（<100ms）
- 高频写入（MQTT可能每秒多次更新）
- 历史查询允许稍慢（<1秒）

## ✅ 推荐方案：混合存储架构

### 架构设计

```
MQTT消息 
  ↓
更新内存缓存（DEVICE_STATUS字典） ← 实时查询（快速）
  ↓
同时更新MySQL devices表（当前状态） ← 持久化（最新状态）
  ↓
选择性写入MySQL device_status_history表（历史记录） ← 历史查询
```

### 存储策略

| 数据类型 | 存储位置 | 用途 | 更新频率 |
|---------|---------|------|---------|
| **实时状态** | 内存（DEVICE_STATUS字典） | 实时查询显示 | 实时更新 |
| **当前状态** | MySQL `devices` 表 | 持久化最新状态、服务重启恢复 | 实时更新 |
| **历史状态** | MySQL `device_status_history` 表 | 历史查询、统计分析 | 选择性写入（重要变化） |

## 📊 数据表设计

### 1. devices 表（存储当前状态）

```sql
CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL UNIQUE COMMENT '设备编号',
    device_name VARCHAR(200) COMMENT '设备名称',
    status VARCHAR(50) DEFAULT 'unknown' COMMENT '当前状态',
    status_data JSON COMMENT '完整状态数据',
    last_update TIMESTAMP NULL COMMENT '最后更新时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**特点**：
- 每个设备**只有一条记录**（ON DUPLICATE KEY UPDATE）
- 存储**最新状态**
- 查询速度快（索引优化）

### 2. device_status_history 表（存储历史记录）

```sql
CREATE TABLE device_status_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL COMMENT '设备编号',
    status VARCHAR(50) NOT NULL COMMENT '设备状态',
    status_data JSON COMMENT '完整状态数据',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '状态时间',
    INDEX idx_device_timestamp (device_id, timestamp),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**特点**：
- 存储**历史变化**
- 可选择性写入（只存重要状态变化，避免数据过多）
- 支持历史查询和统计分析

## 💡 实现方案

### MQTT消息处理逻辑

```python
# app/mqtt_client.py

def process_device_message(data):
    """处理设备状态消息"""
    try:
        device_id = data.get('device_id', data.get('deviceId', 'unknown'))
        status = data.get('status', 'unknown')
        timestamp = data.get('timestamp', time.time())
        
        # ========== 1. 更新内存缓存（实时查询用） ==========
        DEVICE_STATUS[device_id] = {
            'status': status,
            'last_update': timestamp,
            'data': data
        }
        # 内存查询速度：< 1ms ✅
        
        # ========== 2. 更新MySQL当前状态表（持久化） ==========
        update_device_current_status(device_id, status, data, timestamp)
        # MySQL UPSERT操作：10-50ms ✅
        
        # ========== 3. 选择性写入历史记录（重要状态变化） ==========
        if should_save_history(device_id, status):
            save_device_status_history(device_id, status, data, timestamp)
        # MySQL INSERT操作：5-20ms ✅
        
        print(f"📊 设备状态更新: {device_id} -> {status}")
        
    except Exception as e:
        print(f"处理设备消息失败: {e}")

def update_device_current_status(device_id, status, data, timestamp):
    """更新设备当前状态到MySQL"""
    db = get_db()
    if not db:
        return
    
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO devices (device_id, status, status_data, last_update)
                VALUES (%s, %s, %s, FROM_UNIXTIME(%s))
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    status_data = VALUES(status_data),
                    last_update = VALUES(last_update),
                    updated_at = NOW()
            """, (device_id, status, json.dumps(data), timestamp))
            db.commit()
    except Exception as e:
        print(f"更新设备状态失败: {e}")
        db.rollback()
    finally:
        db.close()

def should_save_history(device_id, status):
    """判断是否需要保存历史记录"""
    # 策略1：只保存重要状态变化
    important_statuses = ['error', 'offline', 'online', 'overload', 'warning']
    if status in important_statuses:
        return True
    
    # 策略2：如果状态发生变化（可选）
    last_status = DEVICE_STATUS.get(device_id, {}).get('status')
    if last_status != status:
        return True
    
    return False

def save_device_status_history(device_id, status, data, timestamp):
    """保存设备状态历史记录"""
    db = get_db()
    if not db:
        return
    
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO device_status_history 
                (device_id, status, status_data, timestamp)
                VALUES (%s, %s, %s, FROM_UNIXTIME(%s))
            """, (device_id, status, json.dumps(data), timestamp))
            db.commit()
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        db.rollback()
    finally:
        db.close()
```

### API查询逻辑

```python
# app/routes/mp.py 或 server.py

@app.route('/api/mp/device-status', methods=['GET'])
def mp_get_device_status():
    """获取设备状态 - 从内存读取（快速）"""
    try:
        # 直接从内存读取，速度最快
        from app.mqtt_client import get_device_status
        devices = get_device_status()
        
        return jsonify({
            "devices": devices,
            "total": len(devices)
        }), 200
    except Exception as e:
        return jsonify({"msg": "获取设备状态失败"}), 500

@app.route('/api/device-status-history', methods=['GET'])
def get_device_status_history():
    """获取设备历史状态 - 从MySQL读取"""
    device_id = request.args.get('device_id')
    limit = int(request.args.get('limit', 100))
    
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            if device_id:
                cursor.execute("""
                    SELECT * FROM device_status_history
                    WHERE device_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (device_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM device_status_history
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
            
            history = cursor.fetchall()
            return jsonify({"history": history}), 200
    except Exception as e:
        return jsonify({"msg": "查询失败"}), 500
```

## 📈 性能对比

### 方案A：只用内存（当前方案）
- ✅ 查询速度：< 1ms（最快）
- ❌ 服务重启数据丢失
- ❌ 无法查询历史
- ❌ 无法关联审批记录

### 方案B：只用MySQL
- ✅ 持久化
- ✅ 可查历史
- ❌ 查询速度：10-100ms（较慢）
- ❌ 高频写入可能影响性能

### 方案C：混合方案（推荐）⭐
- ✅ 查询速度：< 1ms（从内存读取）
- ✅ 持久化（MySQL存储）
- ✅ 可查历史（MySQL历史表）
- ✅ 可关联审批记录
- ✅ 服务重启后可从MySQL恢复

## 🚀 服务启动时恢复数据

```python
def init_device_status_from_db():
    """服务启动时从MySQL恢复设备状态到内存"""
    db = get_db()
    if not db:
        return
    
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT device_id, status, status_data, last_update
                FROM devices
                WHERE last_update > DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)
            devices = cursor.fetchall()
            
            for device in devices:
                DEVICE_STATUS[device['device_id']] = {
                    'status': device['status'],
                    'last_update': device['last_update'].timestamp(),
                    'data': json.loads(device['status_data']) if device['status_data'] else {}
                }
            
            print(f"✅ 从数据库恢复 {len(devices)} 个设备状态")
    except Exception as e:
        print(f"❌ 恢复设备状态失败: {e}")
    finally:
        db.close()
```

## 📝 总结

**推荐方案**：**混合存储架构**

1. **实时查询** → 从内存（DEVICE_STATUS字典）读取 ⚡
2. **持久化** → 同时写入MySQL devices表 💾
3. **历史查询** → 从MySQL device_status_history表读取 📊
4. **服务恢复** → 启动时从MySQL恢复最新状态 🔄

**优势**：
- ✅ 实时查询速度快（内存）
- ✅ 数据持久化（MySQL）
- ✅ 支持历史查询（MySQL历史表）
- ✅ 可关联审批记录
- ✅ 服务重启不丢数据

**性能影响**：
- 查询性能：**几乎无影响**（仍然从内存读取）
- 写入性能：**影响很小**（MySQL UPSERT操作很快）
- 数据量：**可控**（历史表选择性写入）
