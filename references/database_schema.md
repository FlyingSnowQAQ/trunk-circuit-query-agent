# 数据库 Schema 参考文档

## circuits 表 — 电路摘要

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `circuit_no` | TEXT | 电路编号，核心查询字段 |
| `system_name` | TEXT | 传输系统名称（如 "北京-上海39系统"） |
| `circuit_name` | TEXT | 电路名称（如 "上海JS1-北京JS1"） |
| `endpoint` | TEXT | 终端点（如 "浦东-大白楼"） |
| `project_phase` | TEXT | 建设期（如 "10期", "13期"） |
| `system_type` | TEXT | 系统性质（IP/SDH/CMNET） |
| `capacity` | TEXT | 容量（如 "1+1 10G POS"） |
| `protection_type` | TEXT | 保护类型 |
| `service_type` | TEXT | 业务种类 |
| `business_nature` | TEXT | 业务性质 |
| `route_nature` | TEXT | 路由性质（主用/备用） |
| `protection_circuit` | TEXT | 保护电路编号 |
| `protection_endpoint` | TEXT | 保护电路终端点 |
| `source_file` | TEXT | 来源文件（追溯用） |
| `source_sheet` | TEXT | 来源 sheet |
| `update_date` | TEXT | 数据更新时间 |
| `remark` | TEXT | 备注 |
| `raw_json` | TEXT | 原始行数据 JSON |

**索引**: `system_name`, `circuit_name`, `circuit_no`, `project_phase`

---

## circuit_hops 表 — 路由跳段详情

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `circuit_no` | TEXT | 关联电路编号 |
| `system_name` | TEXT | 关联系统名称 |
| `circuit_name` | TEXT | 电路名称（迁移后回填） |
| `project_phase` | TEXT | 建设期（补全脚本填充） |
| `hop_order` | INTEGER | 跳次序号 |
| `route_type` | TEXT | 主用/备用 |
| `station_a` | TEXT | A 端局站 |
| `station_b` | TEXT | B 端局站 |
| `timeslot_id` | TEXT | 时隙 ID（如 "M7578λ31-1"） |
| `multiplex_section` | TEXT | 复用段名称 |
| `device_type` | TEXT | 设备类型（如 "OSN9800"） |
| `a_equipment_id` | TEXT | A 网元 ID |
| `a_line_slot` | TEXT | A 线路槽位 |
| `a_line_port` | TEXT | A 线路端口 |
| `a_line_board` | TEXT | A 线路板类型 |
| `a_tributary_slot` | TEXT | A 支路槽位 |
| `a_tributary_port` | TEXT | A 支路端口 |
| `a_tributary_board` | TEXT | A 支路板类型 |
| `b_equipment_id` | TEXT | B 网元 ID |
| `b_line_slot` | TEXT | B 线路槽位 |
| `b_line_port` | TEXT | B 线路端口 |
| `b_line_board` | TEXT | B 线路板类型 |
| `b_tributary_slot` | TEXT | B 支路槽位 |
| `b_tributary_port` | TEXT | B 支路端口 |
| `b_tributary_board` | TEXT | B 支路板类型 |
| `board_type_a` | TEXT | A 端单盘名称（补全） |
| `board_type_b` | TEXT | B 端单盘名称（补全） |
| `source_file` | TEXT | 来源文件 |
| `source_sheet` | TEXT | 来源 sheet |
| `raw_json` | TEXT | 原始行数据 JSON |

**索引**: `circuit_no`, `system_name`, `circuit_name`

---

## multiplex_sections 表 — 复用段链路

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `project_phase` | TEXT | 建设期 |
| `system_name` | TEXT | 关联系统名 |
| `link_id` | TEXT | 链路 ID |
| `province` | TEXT | 省份 |
| `station` | TEXT | 局站 |
| `device_type` | TEXT | 设备类型 |
| `platform` | TEXT | 平台 |
| `timeslot_id` | TEXT | 时隙 ID |
| `multiplex_section_name` | TEXT | 复用段名称 |
| `config_phase` | TEXT | 配置期 |
| `use_phase` | TEXT | 使用期 |
| `usage_type` | TEXT | 本期使用（新建/利旧） |
| `usage_nature` | TEXT | 使用性质（工作/保护） |
| `terminal_type` | TEXT | 终端/转接 |
| `rate` | TEXT | 速率 |

---

## 表间关系

```
circuits (circuit_no, system_name, circuit_name, project_phase)
    │
    │ JOIN ON circuit_no / system_name / circuit_name
    ▼
circuit_hops (circuit_no, system_name, circuit_name, station_a, station_b, ...)
    │
    │ JOIN ON system_name
    ▼
multiplex_sections (system_name, project_phase, multiplex_section_name, ...)
```

- **路由查询流程**: circuits 表定位电路 → 通过 circuit_no / circuit_name / system_name 关联到 circuit_hops → 获取路由跳段详情
- **数据来源**: circuits 表来自汇总 Excel（1-移动干线电路名称汇总.xlsx），circuit_hops 表来自各期光通道路由表
