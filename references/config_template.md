# 配置模板

## 环境变量配置

系统通过环境变量进行配置，以下是完整的环境变量说明：

```bash
# ========== 数据库路径 ==========
# 指向已构建好的 SQLite 数据库文件
# 默认：circuit-query-system/output/circuits.db
set CIRCUIT_DB_PATH=D:\data\circuits.db

# ========== DeepSeek API 配置（可选）==========
# 配置后启用 AI 意图识别和格式化总结功能
set DEEPSEEK_API_KEY=sk-your-api-key-here
set DEEPSEEK_BASE_URL=https://api.deepseek.com
set DEEPSEEK_MODEL=deepseek-chat

# ========== API 服务配置 ==========
set CIRCUIT_API_HOST=0.0.0.0
set CIRCUIT_API_PORT=8000

# ========== 智能体配置 ==========
# 设为 false 禁用 LLM（纯 SQL 降级模式）
set ENABLE_LLM=true
```

## config.py 模板

项目自带 `config.py` 文件，关键配置项说明：

```python
# 数据库路径（默认指向已构建的 DB）
DB_PATH = os.environ.get("CIRCUIT_DB_PATH", "default/path/circuits.db")

# DeepSeek API
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# 服务监听
API_HOST = os.environ.get("CIRCUIT_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("CIRCUIT_API_PORT", "8000"))

# 智能体开关
ENABLE_LLM = os.environ.get("ENABLE_LLM", "true").lower() == "true"
LLM_TEMPERATURE = 0.1
```

## 快速启动配置模板

创建 `start.bat` 一鍵启动脚本的配置部分：

```batch
@echo off
chcp 65001 >nul
title 移动干线电路查询智能体

:: 设置数据库路径（如果数据库不在默认位置）
set CIRCUIT_DB_PATH=D:\data\circuits.db

:: 设置 DeepSeek API 密钥（如需 AI 功能）
set DEEPSEEK_API_KEY=sk-your-api-key-here

:: 清除环境变量冲突
set PYTHONHOME=
set PYTHONPATH=

cd /d "%~dp0"

:: 安装依赖
pip install -r requirements.txt

:: 启动服务
python -m api.server
```
