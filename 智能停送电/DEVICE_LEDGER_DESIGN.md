# 设备标准台账设计说明

更新时间：2026-03-27

## 1. 文档目的

这份文档用于明确“设备标准台账”在当前停送电系统里的作用、字段设计、数据来源、功能价值和落地顺序。

当前系统已经具备：

- 停送电申请与审批
- 验电、检修、送电申请
- 挂牌和送电前校验
- 大检修批次
- 设备监控页面

但这些能力目前仍偏“流程平台”。

如果要进一步升级成“以设备为中心的停送电管理平台”，就必须引入一套统一、可维护、可扩展的设备标准台账。

---

## 2. 什么是设备标准台账

设备标准台账不是简单的“设备列表”。

它是系统中所有设备的统一主数据中心，用来把以下信息挂到同一个设备上：

- 设备基础身份
- 所属配电室和柜位
- 系统图位置
- 远程/就地信号
- 分合闸反馈
- 带电状态反馈
- 故障信号
- 工单、审批、挂牌、检修记录
- 二维码档案信息

一句话理解：

设备标准台账就是整个停送电系统的“设备主键和设备画像”。

---

## 3. 当前为什么需要它

现在系统虽然已经有 `devices` 表，但字段还偏轻，主要用于页面展示和工单关联。

一旦引入标准台账，可以立刻增强这些能力：

1. 停送电申请时更准确地搜索和选择设备
2. 让审批、工单、监控、挂牌围绕同一设备联动
3. 为“已失电免审批安全确认挂牌”提供更可信的判定依据
4. 为远程/就地、分合闸反馈、故障反馈建立信号映射
5. 为二维码设备档案提供数据基础
6. 为监控系统图、报表、批次检修提供真实设备主数据

---

## 4. 现有来源文件有什么价值

### 4.1 `停送电信号表.xlsx`

这个文件的直接价值非常高，适合作为第一版标准台账的数据来源。

当前已确认可以从中提取出：

- 设备编号
- 设备名称
- 图号或系统图来源
- 远程/就地信号
- PLC 地址或 DB 地址
- 部分显示名或简称
- 部分“远程分合闸”点位映射

已实际读到的样例包括：

- `404 / 块煤系统喷水泵`
- `301 / 原煤储煤场送至主厂房带式输送机`
- `121 / 机头间至原煤储煤场带式输送机`
- `311y / 块精煤破碎机油泵电机`
- `DB162,DBB0`
- `I0.7`
- `远程/就地`

说明这个文件不仅能补设备名，还能补信号映射。

### 4.2 `主厂房变电所电气设备安装2023-09-17.dwg`

这个文件更适合作为系统图和设备布局校准依据。

它的价值主要体现在：

- 校准配电室、柜位、回路结构
- 确认系统图上设备的真实位置
- 后续还原更接近现场的单线图监控页面

它不如 `xlsx` 适合直接导入数据库，但非常适合做结构校对。

---

## 5. 标准台账能直接带来的功能

### 5.1 停送电申请增强

可以支持：

- 按设备编号搜索
- 按设备名称搜索
- 按简称搜索
- 按配电室筛选
- 按柜号筛选
- 按工艺区域筛选
- 默认带出本人负责设备

### 5.2 审批与监控联动

每个工单都能精准挂到一个标准设备上，后续可以做到：

- 审批页查看当前设备状态
- 工单详情跳转设备监控定位
- 审批记录按设备追溯

### 5.3 已失电免审批安全确认流程

现在系统已经支持：

- 设备已失电时跳过停电审批
- 转入“待电工安全确认并挂牌”

如果有标准台账，就能进一步明确：

- 哪个点位代表失电
- 哪个点位代表分闸
- 哪个设备允许免审批
- 哪个设备必须保留人工确认

### 5.4 设备监控真实化

系统图页可以不再只是卡片列表，而是基于真实台账展示：

- 配电室
- 柜号
- 母线
- 回路
- 设备顺序

### 5.5 二维码设备档案

甲方要求里的二维码模块，本质上就是标准台账的延伸。

扫码后可以看到：

- 基础信息
- 型号和功率
- 操作说明
- 空载电流
- 重载电流
- 保养记录
- 检修记录
- 备品备件信息

### 5.6 大检修批次优化

批次检修后续可以按：

- 配电室
- 工艺段
- 设备组
- 系统图区域

做更真实的批量选设备，而不是单纯一台台勾选。

### 5.7 报表和导出

有标准台账之后，可以生成：

- 按设备停送电次数统计
- 按配电室检修频次统计
- 按回路故障统计
- 按设备挂牌风险统计
- 按区域检修完成率统计

---

## 6. 第一版标准台账建议字段

### 6.1 基础身份字段

必备字段：

- `device_id`
- `device_name`
- `device_alias`
- `display_name`
- `is_active`

说明：

- `device_id`：设备唯一编码，如 `404`、`311y`
- `device_name`：正式设备名称
- `device_alias`：页面展示简称，例如 `404循环水泵`
- `display_name`：系统图和列表页的统一展示名

### 6.2 位置与结构字段

建议字段：

- `power_room`
- `cabinet`
- `area_code`
- `line_name`
- `system_diagram_name`
- `sort_order`

说明：

- `power_room`：如主厂房、产品仓
- `cabinet`：所属柜位或 MCC
- `line_name`：母线、回路、馈线等
- `system_diagram_name`：系统图一、系统图二等
- `sort_order`：系统图上的排序

### 6.3 信号映射字段

这是标准台账最关键的增强部分。

建议字段：

- `remote_local_signal`
- `power_feedback_signal`
- `trip_feedback_signal`
- `close_feedback_signal`
- `fault_signal`
- `run_mode_signal`
- `current_a_signal`
- `current_b_signal`
- `current_c_signal`

说明：

- `remote_local_signal`：远程/就地状态点
- `power_feedback_signal`：带电/失电反馈点
- `trip_feedback_signal`：分闸反馈点
- `close_feedback_signal`：合闸反馈点
- `fault_signal`：故障反馈点
- `run_mode_signal`：变频/工频反馈点
- `current_*_signal`：三相电流点位

### 6.4 控制策略字段

建议字段：

- `is_remote_controllable`
- `allow_skip_power_off_approval`
- `requires_dual_confirm`
- `is_key_device`
- `requires_field_check`

说明：

- `allow_skip_power_off_approval`：是否允许已失电免审批
- `requires_dual_confirm`：是否必须双人确认
- `requires_field_check`：是否必须现场复核

### 6.5 设备档案字段

为二维码和运维档案预留：

- `model`
- `power_rating`
- `motor_model`
- `reducer_model`
- `no_load_current`
- `full_load_current`
- `operation_guide`
- `spare_parts_info`
- `maintenance_notes`

---

## 7. 推荐的数据表设计

### 7.1 主表：`devices`

建议保留并扩展为设备主表。

建议新增或补强这些字段：

```sql
devices (
  id bigint primary key,
  device_id varchar(64) unique,
  device_name varchar(255),
  device_alias varchar(255),
  display_name varchar(255),
  power_room varchar(128),
  cabinet varchar(128),
  area_code varchar(64),
  line_name varchar(128),
  system_diagram_name varchar(128),
  sort_order int,
  is_active boolean,
  is_remote_controllable boolean,
  allow_skip_power_off_approval boolean,
  requires_dual_confirm boolean,
  is_key_device boolean,
  requires_field_check boolean,
  model varchar(128),
  power_rating varchar(64),
  motor_model varchar(128),
  reducer_model varchar(128),
  no_load_current varchar(64),
  full_load_current varchar(64),
  operation_guide text,
  spare_parts_info text,
  maintenance_notes text,
  created_at datetime,
  updated_at datetime
)
```

### 7.2 信号表：`device_signal_points`

不建议把所有信号都塞进 `devices`，后续会很难维护。

建议拆表：

```sql
device_signal_points (
  id bigint primary key,
  device_id bigint,
  signal_type varchar(64),
  signal_name varchar(255),
  signal_address varchar(128),
  data_type varchar(64),
  source_system varchar(64),
  description varchar(255),
  is_active boolean,
  created_at datetime,
  updated_at datetime
)
```

`signal_type` 可取值：

- `remote_local`
- `power_feedback`
- `trip_feedback`
- `close_feedback`
- `fault_feedback`
- `run_mode`
- `current_a`
- `current_b`
- `current_c`

### 7.3 设备二维码档案扩展表

后续如果二维码信息越来越多，可以再拆：

```sql
device_profiles (
  id bigint primary key,
  device_id bigint,
  qr_code varchar(128),
  operation_spec text,
  spare_parts_info text,
  maintenance_standard text,
  created_at datetime,
  updated_at datetime
)
```

---

## 8. `停送电信号表.xlsx` 到标准台账的映射建议

### 8.1 当前可稳定提取的字段

从当前已看到的工作表内容，可以先做第一版映射：

| Excel内容 | 标准台账字段 |
|---|---|
| 设备编号 | `device_id` |
| 设备名称 | `device_name` |
| 简称或组合显示名 | `device_alias` / `display_name` |
| 图号 / 系统图信息 | `system_diagram_name` |
| DB地址 | `signal_address` |
| 远程/就地 | `signal_type = remote_local` |
| 远程分合闸逻辑名 | `signal_name` / `signal_type` |

### 8.2 当前需人工校对的字段

这些字段大概率要结合 `dwg` 或现场台账人工补充：

- 配电室
- 柜号
- 母线或回路名称
- 系统图排序
- 是否关键设备
- 是否允许免审批

### 8.3 当前不建议直接自动导入的内容

以下内容建议人工校验后再落库：

- 变频/工频判定逻辑
- 分闸/合闸控制逻辑
- 设备控制权限策略
- 是否允许远程停送电

因为这些字段一旦错，后续会影响安全逻辑。

---

## 9. 推荐落地顺序

### 第一阶段：主数据标准化

目标：

- 替换假设备名
- 统一真实设备编号
- 建立基础位置字段
- 建立显示名规则

产出：

- 干净的设备主表
- 申请页、监控页、批次页都使用真实设备名

### 第二阶段：信号点位标准化

目标：

- 导入远程/就地点位
- 导入带电、分合闸、故障反馈点位
- 建立设备与信号的绑定关系

产出：

- 监控页和审批流程真正共享同一套设备信号判断
- 已失电免审批逻辑更可信

### 第三阶段：二维码档案和扩展属性

目标：

- 补型号、功率、空载电流、重载电流
- 补操作说明、备件信息、检修保养标准

产出：

- 二维码设备档案
- 检修运维档案

### 第四阶段：监控系统图真实还原

目标：

- 参考 `dwg` 还原真实布局
- 让设备监控页更像现场单线图

产出：

- 系统图模式下的真实设备位置展示

---

## 10. 对当前系统的直接改造建议

### 10.1 申请页

接入标准台账后，可以新增：

- 按配电室筛选设备
- 按柜号筛选设备
- 已失电设备高亮
- 关键设备单独提醒

### 10.2 审批页

可新增：

- 远程/就地状态列
- 当前带电状态列
- 故障反馈列
- 不允许远程操作的设备高亮阻断

### 10.3 检修页

可新增：

- 安全确认挂牌前显示失电反馈来源
- 显示当前远程/就地状态
- 显示分合闸反馈状态

### 10.4 设备监控页

可新增：

- 三相电流显示
- 变频/工频反馈
- 分合闸反馈
- 就地/远程控制状态
- 故障告警状态

### 10.5 工单详情页

可新增：

- 设备档案摘要
- 当前实时状态快照
- 控制策略说明

---

## 11. 当前最值得优先新增的字段

如果不想一次上太重，建议优先加以下字段：

- `device_alias`
- `display_name`
- `system_diagram_name`
- `remote_local_signal`
- `power_feedback_signal`
- `fault_signal`
- `is_remote_controllable`
- `allow_skip_power_off_approval`
- `is_key_device`

这是投入最小、收益最高的一组。

---

## 12. 实施时的注意事项

### 12.1 不要直接覆盖历史工单的设备文本

历史工单要保留当时的快照信息，避免后续设备更名后看不懂旧记录。

建议：

- 工单仍保留当时的设备显示快照
- 同时继续关联标准设备主表

### 12.2 设备编号要保持唯一

不同图纸、不同系统图里如果存在同名或同号，要统一编号规则。

### 12.3 信号映射必须版本可追溯

PLC 点位、DB 地址变更后，要有版本记录，不然监控和审批逻辑会漂移。

### 12.4 控制策略字段要有人工确认环节

像 `allow_skip_power_off_approval` 这类字段不能自动大量导入，必须人工审核。

---

## 13. 建议的下一步工作

建议按下面顺序推进：

1. 把 `停送电信号表.xlsx` 解析成标准化中间表
2. 清洗设备编号、设备名称、显示名
3. 给 `devices` 和 `device_signal_points` 做迁移
4. 先导入主数据，再导入信号点位
5. 接入申请页、审批页、监控页
6. 最后再推进二维码设备档案

---

## 14. 一句话总结

设备标准台账的核心价值，是把当前“围绕工单流转的审批平台”，升级成“围绕设备运行、停送电控制和检修履历协同的设备管理平台”。
