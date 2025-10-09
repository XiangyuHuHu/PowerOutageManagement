# 服务器迁移计划

## 📊 当前状态分析

### **server.py（原版）**
- ✅ **功能完整**：包含所有API端点
- ✅ **稳定运行**：经过充分测试
- ❌ **代码臃肿**：1753行单体文件
- ❌ **难以维护**：所有功能混在一起

### **server_new.py（新版本）**
- ✅ **模块化设计**：代码结构清晰
- ✅ **易于维护**：功能分离到不同模块
- ❌ **功能不完整**：缺少多个重要API端点
- ❌ **未充分测试**：可能存在未知问题

## 🎯 迁移策略

### **阶段1：功能补全（当前）**
需要在新版本中添加缺少的API端点：

#### **缺少的核心API端点**
```python
# 需要添加到 app/routes/api.py
/api/electrician-verify          # 电工验证
/api/repair-operation           # 检修操作
/api/power-on-apply            # 送电申请
/api/power-on-approve          # 送电审批
/api/application/<int:app_id>   # 申请详情
/api/export/applications        # 导出申请
```

#### **缺少的小程序API端点**
```python
# 需要添加到 app/routes/mp.py
/api/mp/power-apply            # 小程序停电申请
/api/mp/power-on-apply         # 小程序送电申请
/api/mp/my-applications        # 我的申请
/api/mp/application-detail     # 申请详情
/api/mp/approve-application    # 审批申请
/api/mp/reject-application     # 拒绝申请
/api/mp/approve-power-on       # 审批送电
/api/mp/reject-power-on        # 拒绝送电
/api/mp/device-control         # 设备控制
```

### **阶段2：并行运行**
- 保留 `server.py` 作为备用
- 完善 `server_new.py` 功能
- 逐步迁移到新版本

### **阶段3：完全迁移**
- 新版本功能完整后
- 充分测试所有功能
- 删除 `server.py`

## 🚀 当前建议

### **✅ 推荐方案：保留两个版本**

#### **开发环境**
```bash
# 使用新版本进行开发
python server_new.py
```

#### **生产环境**
```bash
# 使用原版确保稳定性
python server.py
```

#### **Docker环境**
```bash
# 当前使用新版本
docker compose up --build
```

### **🔧 快速修复方案**

如果需要立即使用新版本，可以：

1. **复制缺失的API端点**：
   ```bash
   # 从server.py复制缺失的端点到app/routes/
   ```

2. **保持原版作为备用**：
   ```bash
   # 需要时可以快速切换
   # python server.py  # 原版
   # python server_new.py  # 新版本
   ```

## 📋 迁移检查清单

### **功能完整性检查**
- [ ] 所有API端点已实现
- [ ] 数据库操作正常
- [ ] MQTT功能正常
- [ ] 通知功能正常
- [ ] 权限控制正常

### **测试检查**
- [ ] Web端功能测试
- [ ] 小程序功能测试
- [ ] 用户管理测试
- [ ] 设备监控测试
- [ ] 通知系统测试

### **性能检查**
- [ ] 响应时间正常
- [ ] 内存使用合理
- [ ] 并发处理正常
- [ ] 错误处理完善

## 🎉 结论

**建议暂时保留 `server.py`**，原因：

1. **功能完整性**：原版包含所有必要功能
2. **稳定性**：经过充分测试，运行稳定
3. **备用方案**：如果新版本出现问题，可以快速回退
4. **渐进迁移**：可以逐步完善新版本功能

**当前最佳实践**：
- 开发时使用 `server_new.py`
- 生产环境保留 `server.py` 作为备用
- 逐步完善新版本功能
- 功能完整后再考虑完全迁移 