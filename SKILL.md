---
name: trunk-circuit-query-agent
description: 中国移动一干传输电路路由查询智能体。当用户需要查询传输系统路由（输入系统名或电路编号自动识别所属工程期数并返回路由跳段详情）时使用。适用于网络运维人员对移动一干400G/OTN网络的日常巡检、故障定位和路由信息查询。
agent_created: true
---

# 移动干线电路查询智能体 (Trunk Circuit Query Agent)

## Overview

中国移动一干传输电路路由查询系统，提供 "传输系统名 → 电路名称汇总查工程期数 → 期数路由表查路由跳段" 的三步推理查询能力。

**核心流程**:
1. 识别用户输入中的传输系统名或电路编号
2. 在电路名称汇总表中查询所属工程期数
3. 到对应期数的路由表中查询路由跳段详情（返回 ALL 匹配行）

## Core Capabilities

### 1. 智能体三步查询

通过 FastAPI 服务暴露，支持自然语言输入：

- 输入 "查一下北京-上海39系统" → 输出该电路属于**10期**工程及其路由跳段
- 输入 "4950" → 自动定位到电路 4950 的详情
- 输入 "W-239" → 模糊匹配后识别为对应系统名

**查询策略（三级匹配）**:
1. `circuit_no` 精确匹配 — 最高优先级
2. `circuit_name` 关键词 LIKE 匹配 — 解决跨表名称顺序不一致问题（如 "上海JS1-北京JS1" vs "北京JS1-上海JS1"）
3. `system_name` LIKE 模糊匹配 — 兜底

### 2. 降级模式

未配置 DeepSeek API 时自动降级为纯 SQL 查询模式：
- 自然语言前缀清洗（"查一下"、"找找" 等自动去除）
- 所有核心功能正常可用，仅无 AI 文字总结

### 3. 快捷 API（跳过智能体）

提供 `GET /api/circuits/search` 和 `GET /api/circuits/detail` 端点，可直接调用无需经过 LLM 编排。

## Quick Start

### 前提条件

1. 已构建的 SQLite 数据库文件（`circuits.db`，约 200-300MB）
2. Python 3.10+
3. 依赖安装：`pip install -r requirements.txt`

### 启动服务

```bash
# 清理环境变量冲突后启动
PYTHONHOME="" PYTHONPATH="" python -m api.server
```

或用脚本启动：
```bash
python scripts/start_server.py
```

### 验证

```bash
curl http://localhost:8000/api/health
```

## Assets Structure

### assets/ — 项目核心文件

```
assets/
├── agent/              # 智能体引擎（tools.py, engine.py, llm_client.py）
│   ├── tools.py        # 核心工具（lookup_phase, query_routing, search_circuits）
│   ├── engine.py       # 编排引擎（run_agent 三步推理）
│   └── llm_client.py   # DeepSeek API 封装
├── api/                # FastAPI 服务
│   ├── server.py       # 路由注册 + 应用生命周期
│   └── schemas.py      # Pydantic 数据模型
├── web/                # Web UI
│   ├── templates/      # base.html + index.html
│   └── static/         # style.css + ui.js
├── parsers/            # 数据预处理解析器
│   ├── schema.py       # 数据库表结构定义
│   ├── column_mapper.py # 列映射规则
│   └── route_parser.py # 路由表解析器
├── utils/              # 数据库操作工具
├── config.py           # 配置文件
├── requirements.txt    # Python 依赖
├── start.bat           # Windows 一键启动
└── migrate_db.py       # 数据库迁移脚本
```

### references/ — 参考文档

| 文件 | 内容 |
|------|------|
| `database_schema.md` | 数据库表结构（circuits, circuit_hops, multiplex_sections） |
| `api_endpoints.md` | REST API 端点参考（请求/响应示例） |
| `config_template.md` | 环境变量配置模板和示例 |
| `deployment_guide.md` | 从零开始的完整部署指南 |

### scripts/ — 辅助脚本

| 文件 | 功能 |
|------|------|
| `start_server.py` | 启动 API 服务器（自动清理环境变量冲突） |

## Database Information

系统依赖 SQLite 数据库，关键表：

| 表名 | 记录数（参考） | 说明 |
|------|---------------|------|
| `circuits` | 162,840 | 电路摘要（汇总Excel解析） |
| `circuit_hops` | 157,132 | 路由跳段详情（各期路由表解析） |
| `multiplex_sections` | 27,203 | 复用段链路信息 |

更多详见 `references/database_schema.md`。

## Notes

- **路径冲突**: Windows 系统可能存在 `PYTHONHOME` 环境变量冲突，启动前需清理
- **数据质量**: 部分源数据存在脏数据（空 `station_a`/`station_b`、`system_name` 为 "0" 等）
- **DB 迁移**: 对已有数据库运行 `migrate_db.py` 可补全 `circuit_hops.circuit_name` 字段
- **端口**: 默认 8000，与旧版本 Flask 服务（5000）不冲突
