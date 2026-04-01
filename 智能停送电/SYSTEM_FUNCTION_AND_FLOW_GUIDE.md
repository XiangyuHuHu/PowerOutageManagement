# 停送电审批平台整体功能与流程说明

本文档用于系统性说明当前“智能停送电审批平台”的整体功能、角色分工、页面入口、核心流程、批次检修能力、数据关系和典型使用方式。

文档适用对象：

- 项目负责人
- 运维 / 开发 / 测试人员
- 现场管理人员
- 用于内部培训、交接、汇报和演示

更新时间：2026-03-26

---

## 1. 系统定位

本系统是一个围绕“停电申请、审批、验电、检修、送电申请、送电审批”展开的流程平台。

它解决的核心问题有 3 类：

1. 把停送电作业流程从口头沟通变成线上留痕流程
2. 把设备台账、审批状态、挂牌状态和检修进度关联起来
3. 在大检修场景下，支持按配电室集中建单、集中审批、集中看板追踪

系统当前不负责“现场实际断电 / 合闸执行控制”。
现场执行仍按线下作业规程进行，系统负责：

- 审批流转
- 安全状态留痕
- 挂牌状态追踪
- 设备监控展示
- 批次检修组织与管理

---

## 2. 当前系统包含的核心能力

### 2.1 单工单停送电流程

支持单台设备从停电申请到送电完成的完整闭环：

1. 发起停电申请
2. 调度审批停电
3. 电工验电
4. 电工开始检修
5. 电工完成检修
6. 电工发起送电申请
7. 调度审批送电
8. 工单完成

### 2.2 设备主数据管理

系统已经引入设备台账，不再只是一个设备编号字符串。

当前设备信息可关联：

- 设备编号
- 设备名称
- 配电室
- 柜号
- 区域编码
- 线路名称

这意味着后续审批、监控、批量审批、批次检修都能以“设备主数据”为统一基准。

### 2.3 多人挂牌与解牌管理

系统支持：

- 验电后自动建立本人挂牌记录
- 一个设备可存在多条有效挂牌
- 送电申请前自动尝试解除“本人挂牌”
- 若仍有其他人挂牌，则阻止进入送电审批
- 批量送电审批时也会逐条检查挂牌

### 2.4 批量审批

支持两类批量审批：

- 审批中心按配电室批量审批
- 大检修批次按批次范围批量审批

当前已经修正了早期“按配电室误伤其他工单”的问题。
现在批次看板内的批量审批只会处理当前批次内的工单。

### 2.5 大检修批次

大检修批次用于解决“同一配电室、同一轮计划检修、多台设备同时处理”的场景。

支持能力包括：

- 批量选设备
- 一次生成一组停电工单
- 批次工作台汇总查看
- 批次看板跟踪进度
- 批次级停电 / 送电批量审批
- 批次导出
- 批次完成条件校验

### 2.6 审批记录与操作留痕

系统通过 `application_logs` 留存审批和流程轨迹，支持查看：

- 停电申请
- 停电审批
- 验电
- 开始检修
- 完成检修
- 送电申请
- 送电审批
- 批量审批相关日志

### 2.7 设备监控

支持两种展示模式：

- 系统图模式
- 列表模式

监控页会结合设备台账和实时状态展示：

- 在线 / 离线
- 带电 / 失电
- 挂牌 / 未挂牌
- 告警状态

并且已经支持从批次看板或工单详情跳转并定位设备。

### 2.8 用户权限与范围控制

系统已经具备：

- 角色权限
- 功能权限
- 配电室范围权限

当前支持的角色主要包括：

- 管理员
- 调度员
- 电工
- 普通用户

当前支持的功能权限包括：

- `approval_center`
- `batch_approval`
- `device_monitor`
- `notifications`
- `stats`
- `user_management`
- `batch_management`
- `apply`
- `repair`
- `power_on_apply`
0
---

## 3. 角色与职责

## 3.1 管理员

管理员是平台的全局管理角色，主要职责：

- 查看系统总体情况
- 管理用户和权限
- 创建和管理大检修批次
- 查看审批记录
- 查看系统统计
- 查看设备监控

主要页面：

- `admin.html`
- `user_management.html`
- `stats.html`
- `maintenance_batches.html`
- `maintenance_batch_detail.html`
- `approval_history.html`
- `device_monitor.html`

## 3.2 调度员

调度员负责审批中心和批量审批，是流程中最核心的审批角色。

主要职责：

- 审批停电申请
- 审批送电申请
- 按配电室批量审批
- 按批次批量审批
- 查看审批记录
- 查看设备监控

主要页面：

- `dispatcher_home.html`
- `approval.html`
- `approval_history.html`
- `device_monitor.html`
- `maintenance_batch_detail.html`

## 3.3 电工

电工负责执行阶段流程，不直接审批停送电。

主要职责：

- 查看与本人相关的工单
- 验电
- 开始检修
- 完成检修
- 发起送电申请
- 查看设备监控

主要页面：

- `electrician_home.html`
- `repair.html`
- `power_on_apply.html`
- `detail.html`
- `device_monitor.html`

## 3.4 普通用户

普通用户主要负责发起停电申请。

主要职责：

- 发起停电申请
- 查看个人工单
- 接收通知

主要页面：

- `apply.html`
- `detail.html`
- `notifications.html`

---

## 4. 页面与功能入口

## 4.1 统一入口

系统登录成功后会先进入：

- `home.html`

该页面会根据当前角色自动跳转到对应工作台。

## 4.2 登录与注册

- `login.html`
- `register.html`

登录成功后会写入本地登录态并跳转角色首页。

## 4.3 管理员页

- `admin.html`

管理员首页汇总系统主要入口：

- 审批管理
- 审批记录
- 大检修批次
- 用户权限
- 设备监控
- 系统通知

## 4.4 调度工作台

- `dispatcher_home.html`

主要展示：

- 待停电审批
- 待送电审批
- 挂牌风险工单
- 未读通知
- 重点配电室
- 最近待处理工单

## 4.5 电工工作台

- `electrician_home.html`

主要展示：

- 我的相关工单
- 待验电
- 检修中
- 可发起送电申请工单
- 通知

## 4.6 停电申请页

- `apply.html`

主要用于：

- 选择设备
- 填写停电原因
- 填写计划停送电时间
- 填写操作任务
- 提交停电申请

## 4.7 审批中心

- `approval.html`

主要用于：

- 查看待审批工单
- 单条审批
- 按配电室批量审批
- 查看工单风险和剩余挂牌

## 4.8 电工操作页

- `repair.html`

主要用于：

- 验电确认
- 开始检修
- 完成检修
- 查看详情
- 发起送电申请入口联动

## 4.9 送电申请页

- `power_on_apply.html`

主要用于：

- 查看检修完成的工单
- 查看剩余挂牌
- 查看阻塞原因
- 提交送电申请

## 4.10 工单详情页

- `detail.html`

主要用于：

- 查看工单完整信息
- 查看设备定位
- 查看有效挂牌
- 查看流程轨迹
- 反查所属批次
- 跳转设备监控

## 4.11 审批记录页

- `approval_history.html`

主要用于：

- 查看真实审批流水
- 按工单筛选
- 按批次筛选
- 按操作类型查看流程痕迹

## 4.12 设备监控页

- `device_monitor.html`

主要用于：

- 系统图模式查看设备状态
- 列表模式查看设备状态
- 查看告警
- 从工单或批次看板定位设备

## 4.13 大检修批次页

- `maintenance_batches.html`

主要用于：

- 创建批次
- 选择配电室和设备
- 查看批次列表
- 筛选批次状态

## 4.14 大检修批次详情页

- `maintenance_batch_detail.html`

主要用于：

- 查看批次汇总
- 查看设备级进度
- 查看阻塞原因
- 执行批次级批量审批
- 完成批次
- 导出批次数据

## 4.15 用户权限页

- `user_management.html`

主要用于：

- 查看用户列表
- 修改角色
- 修改功能权限
- 修改配电室范围
- 删除用户

## 4.16 系统统计页

- `stats.html`

主要用于：

- 查看工单总量
- 查看审批率
- 查看角色分布
- 查看最近活动

## 4.17 通知页

- `notifications.html`

主要用于：

- 查看通知列表
- 标记已读
- 批量已读

---

## 5. 单工单业务流程

下面是当前单台设备的标准流程。

## 5.1 停电申请

页面：

- `apply.html`

接口：

- `POST /api/power-apply`

动作：

1. 申请人选择设备
2. 填写停电原因、计划停电时间
3. 提交申请

工单状态变化：

- `pending`

系统动作：

- 生成一条 `applications` 记录
- 写入 `application_logs`
- 通知调度员
- 通知申请人“已提交”

## 5.2 停电审批

页面：

- `approval.html`

接口：

- `POST /api/power-off-approve`

动作：

1. 调度员查看待审批工单
2. 选择通过或驳回
3. 驳回必须填写意见

状态变化：

- 通过：`pending -> approved`
- 驳回：`pending -> rejected`

系统动作：

- 写入审批日志
- 保留审批意见

## 5.3 电工验电

页面：

- `repair.html`

接口：

- `POST /api/electrician-verify`

动作：

1. 电工确认安全措施
2. 提交验电确认

状态变化：

- `approved -> verified`

系统动作：

- 记录验电人
- 记录安全措施
- 自动创建本人挂牌记录

## 5.4 开始检修

页面：

- `repair.html`

接口：

- `POST /api/repair-operation`

动作：

1. 电工点击“开始检修”

状态变化：

- `verified -> repairing`

系统动作：

- 记录检修开始时间
- 写入流程日志

## 5.5 完成检修

页面：

- `repair.html`

接口：

- `POST /api/repair-operation`

动作：

1. 电工点击“完成检修”

状态变化：

- `repairing -> repair_completed`

系统动作：

- 记录检修完成时间
- 写入流程日志

## 5.6 送电申请

页面：

- `power_on_apply.html`

接口：

- `POST /api/power-on-apply`

动作：

1. 电工选择检修完成的工单
2. 查看剩余挂牌和阻塞原因
3. 填写送电原因和计划送电时间
4. 提交送电申请

状态变化：

- 满足条件时：`repair_completed -> power_on_applied`

系统安全逻辑：

1. 系统先尝试解除“本人挂牌”
2. 若仍有其他有效挂牌，不进入送电审批
3. 只有无剩余挂牌时，才允许进入送电审批

## 5.7 送电审批

页面：

- `approval.html`

接口：

- `POST /api/power-on-approve`

动作：

1. 调度员查看待送电审批工单
2. 选择通过或驳回

状态变化：

- 通过：`power_on_applied -> completed`
- 驳回：`power_on_applied -> power_on_rejected`

系统动作：

- 写入审批日志
- 记录审批人、审批时间、审批意见

---

## 6. 大检修批次流程

大检修批次是本系统的重点增强能力。

它不是替代工单，而是把“一轮大修涉及的多台设备工单”组织在一个批次里统一管理。

## 6.1 创建批次

页面：

- `maintenance_batches.html`

接口：

- `POST /api/maintenance-batches`

动作：

1. 管理员填写批次名称
2. 选择配电室
3. 填写计划开始 / 结束时间
4. 填写停电原因和批次说明
5. 选择设备

系统动作：

1. 创建批次记录 `maintenance_batches`
2. 为每台设备生成一条停电工单
3. 建立 `maintenance_batch_devices` 关联

## 6.2 查看批次工作台

页面：

- `maintenance_batches.html`

作用：

- 查看批次状态
- 查看设备数、待审批数、处理中数、风险数
- 快速筛选待处理 / 有风险 / 已完成批次

## 6.3 查看批次看板

页面：

- `maintenance_batch_detail.html`

作用：

- 查看批次摘要
- 查看设备级进度
- 查看挂牌风险设备
- 查看送电阻塞设备
- 查看待处理设备
- 导出批次数据

## 6.4 批次停电批量审批

接口：

- `POST /api/maintenance-batches/<batch_id>/approve`

参数概念：

- `stage=power_off`
- `action=approve/reject`

作用：

- 对当前批次内所有 `pending` 工单执行停电审批

## 6.5 批次送电批量审批

接口：

- `POST /api/maintenance-batches/<batch_id>/approve`

参数概念：

- `stage=power_on`
- `action=approve/reject`

作用：

- 对当前批次内所有 `power_on_applied` 工单执行送电审批

关键安全逻辑：

- 若某条工单仍有挂牌，会被自动跳过
- 不会因为批量审批而绕过单工单安全规则

## 6.6 完成批次

接口：

- `POST /api/maintenance-batches/<batch_id>/close`

只有满足以下条件时才允许完成批次：

1. 全部设备已生成工单
2. 所有工单进入终态
3. 没有处理中工单
4. 没有剩余挂牌

不满足时，接口会返回阻塞原因。

---

## 7. 当前批次状态说明

系统当前支持以下批次状态：

- `draft`
- `generated`
- `in_progress`
- `completed`

含义如下：

### `draft`

批次刚建立，尚未完全生成工单。

### `generated`

批次和批次下工单已经生成，可进入审批与执行阶段。

### `in_progress`

批次内已有工单进入审批后、执行中或待送电审批阶段。

### `completed`

批次内全部工单都进入终态，且当前没有剩余挂牌。

---

## 8. 挂牌与送电安全逻辑

这是当前系统最重要的安全控制点之一。

## 8.1 验电后自动挂牌

电工验电成功后：

- 系统自动为当前电工建立一条有效挂牌记录

## 8.2 支持多人挂牌

同一设备可以存在多条有效挂牌。

这意味着：

- 不能简单用一个布尔值表示“是否挂牌”
- 送电时必须检查全部有效挂牌，而不是只检查当前用户

## 8.3 送电申请先解本人挂牌

电工提交送电申请时：

1. 系统先尝试解除当前电工本人挂牌
2. 再检查设备上是否还存在其他有效挂牌

## 8.4 有剩余挂牌时不能进入送电审批

如果设备仍有其他人挂牌：

- 工单不会进入 `power_on_applied`
- 页面会提示剩余挂牌人
- 需要先完成解牌

## 8.5 批量送电也不绕过安全逻辑

即使是批量送电审批：

- 系统也会逐条检查挂牌
- 有问题的工单只会跳过，不会被强制审批通过

---

## 9. 审批记录与流程留痕

系统主要通过 `application_logs` 留存流程记录。

审批记录页：

- `approval_history.html`

接口：

- `GET /api/approval-history`

当前支持的记录类型包括：

- `create`
- `power_off_approve`
- `electrician_verify`
- `repair_start`
- `repair_end`
- `power_on_apply`
- `power_on_approve`

记录页支持：

- 按工单查看
- 按批次查看
- 查看真实流程日志，而不是靠工单当前状态反推

---

## 10. 设备监控与流程联动

设备监控页：

- `device_monitor.html`

接口：

- `GET /api/device-status`
- `GET /api/device-history`
- `GET /api/device-alerts`

支持能力：

- 系统图模式
- 列表模式
- 设备状态统计
- 告警汇总
- 按配电室定位
- 按设备定位

与业务流程的联动包括：

- 工单详情可跳转设备监控
- 批次看板可跳转设备监控
- 跳转时可自动带上 `device_id` 和 `power_room`

---

## 11. 权限模型

当前权限模型分为 3 层：

## 11.1 角色

- `admin`
- `dispatcher`
- `electrician`
- `user`

## 11.2 功能权限

通过 `user_function_permissions` 控制。

例如：

- 能否进入审批中心
- 能否批量审批
- 能否进入设备监控
- 能否进入用户管理

## 11.3 配电室范围

通过 `user_room_scopes` 控制。

主要用于：

- 限制用户只能查看和处理特定配电室数据

---

## 12. 主要后端接口总览

## 12.1 登录与注册

- `POST /api/login`
- `POST /api/logout`
- `POST /api/register`

## 12.2 工单主流程

- `POST /api/power-apply`
- `GET /api/devices`
- `GET /api/list`
- `POST /api/electrician-verify`
- `POST /api/repair-operation`
- `POST /api/power-on-apply`

## 12.3 审批相关

- `POST /api/power-off-approve`
- `POST /api/power-on-approve`
- `POST /api/batch-approve-room`
- `GET /api/application/<id>`
- `GET /api/approval-history`
- `GET /api/export/applications`

## 12.4 大检修批次

- `GET /api/maintenance-batches`
- `POST /api/maintenance-batches`
- `GET /api/maintenance-batches/<batch_id>`
- `GET /api/maintenance-batches/<batch_id>/export`
- `POST /api/maintenance-batches/<batch_id>/approve`
- `POST /api/maintenance-batches/<batch_id>/close`

## 12.5 用户与系统管理

- `GET /api/users`
- `PUT /api/users/<user_id>`
- `DELETE /api/users/<user_id>`
- `GET /api/permission-options`
- `GET /api/system/metrics`

## 12.6 通知与监控

- `GET /api/notifications`
- `PUT /api/notifications/<id>/read`
- `GET /api/device-status`
- `GET /api/device-history`
- `GET /api/device-alerts`

---

## 13. 主要数据表关系

当前最重要的数据表如下：

### `users`

用户基础信息表。

### `devices`

设备主数据表，提供设备编号、配电室、柜号等信息。

### `applications`

工单主表，是单工单流程的核心表。

### `application_logs`

工单流程日志表，用于追踪审批和操作留痕。

### `device_tag_records`

设备挂牌记录表，用于跟踪多人挂牌和解牌状态。

### `notifications`

用户通知表。

### `user_room_scopes`

用户配电室范围控制表。

### `user_function_permissions`

用户功能权限表。

### `maintenance_batches`

大检修批次主表。

### `maintenance_batch_devices`

批次与设备 / 工单的关联表。

---

## 14. 当前系统的亮点

当前版本相比早期版本，已经完成了这些关键增强：

1. 引入设备主数据，不再只依赖设备编号字符串
2. 审批记录改为真实读取流程日志
3. 关键流程接入统一状态迁移层
4. 支持多人挂牌与安全解牌逻辑
5. 支持按批次的大检修组织方式
6. 批次级停电 / 送电批量审批已收口到当前批次范围
7. 批次完成规则已建立
8. 角色工作台和主要后台页面已基本统一

---

## 15. 当前仍可继续优化的方向

虽然系统目前已经具备完整主链，但后续仍可继续增强：

### 15.1 厂长授权与临时授权

当前权限模型已经有基础，但还可以继续引入：

- 厂长分配权限
- 临时授权
- 更细的数据隔离策略

### 15.2 批次归档 / 取消状态

目前批次支持完成，但还没有：

- 归档
- 取消

### 15.3 实时链路稳定性

设备监控已经有页面和接口，但若要更贴近现场，需要继续补稳：

- MQTT / OPC UA 链路
- 异常恢复
- 实时状态缓存

### 15.4 页面提质

目前主页面已经基本统一，但后续还可以继续做：

- 更统一的空态
- 更明确的禁用原因
- 更完整的操作成功 / 失败反馈

---

## 16. 推荐的演示顺序

如果你要给领导、业务或现场人员演示，建议按下面顺序讲：

1. 登录后进入角色工作台
2. 普通用户发起停电申请
3. 调度员在审批中心审批停电
4. 电工进入工作台完成验电与检修
5. 电工发起送电申请
6. 调度员审批送电
7. 进入工单详情查看流程留痕
8. 进入审批记录查看真实日志
9. 进入设备监控查看设备状态
10. 演示大检修批次：建批次、看看板、批量审批、完成批次

---

## 17. 一句话总结

当前这套平台已经从“单工单审批页”升级成一套包含设备台账、审批流、挂牌追踪、批次检修、权限控制、监控联动和完整留痕能力的停送电流程管理系统。

