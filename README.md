# 移动干线电路查询智能体 (Trunk Circuit Query Agent)

中国移动一干传输电路路由查询智能体 — WorkBuddy Skill Component。

## 功能

- **三步推理查询**: 输入传输系统名 → 电路名称汇总查工程期数 → 期数路由表查路由跳段
- **三级匹配策略**: circuit_no 精确匹配 → circuit_name 关键词 LIKE → system_name 模糊匹配
- **降级模式**: 未配置 LLM 时自动降级为纯 SQL 查询
- **Web UI**: 步骤化卡片展示查询结果
- **REST API**: 支持智能体查询和快捷搜索

## 快速开始

```bash
pip install -r requirements.txt
python -m api.server
# 访问 http://localhost:8000
```

## 项目结构

```
trunk-circuit-query-agent/
├── SKILL.md                 # WorkBuddy Skill 指令文件
├── references/              # 参考文档（数据库Schema、API文档、配置模板、部署指南）
├── scripts/                 # 辅助脚本
└── assets/                  # 项目核心文件
    ├── agent/               # 智能体引擎
    ├── api/                 # FastAPI 服务
    ├── web/                 # Web UI
    ├── parsers/             # 数据预处理解析器
    ├── utils/               # 数据库工具
    ├── config.py            # 配置文件
    └── requirements.txt     # Python 依赖
```

## 数据源

需要以下 Excel 文件构建 SQLite 数据库：
- `1-移动干线电路名称汇总.xlsx` — 电路摘要（15个sheet）
- `2-光通道路由表/` — 各期路由表（7期~17期）

运行 `preprocess.py` 构建数据库，运行 `migrate_db.py` 完成迁移。

## 技术栈

- Python 3.10+ / FastAPI / SQLite / Jinja2
- DeepSeek API（可选，用于AI意图识别）
