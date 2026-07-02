"""
移动干线电路查询智能体 - 配置文件
"""
import os
from pathlib import Path

# ========= 项目根目录 =========
ROOT_DIR = Path(__file__).parent

# ========= 数据库路径 =========
# 默认引用上一轮项目构建好的数据库
# ROOT_DIR = circuit-query-agent/ → parent = 2026-06-17-16-21-06/
# 实际的 DB 在 WorkBuddy/2026-06-17-15-28-15/... 同级下
_DEFAULT_DB = str(
    ROOT_DIR.parent.parent / "2026-06-17-15-28-15" / "circuit-query-system" / "output" / "circuits.db"
)
DB_PATH = os.environ.get("CIRCUIT_DB_PATH", _DEFAULT_DB)

# ========= DeepSeek API 配置 =========
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# ========= API 服务配置 =========
API_HOST = os.environ.get("CIRCUIT_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("CIRCUIT_API_PORT", "8000"))

# ========= 智能体配置 =========
ENABLE_LLM = os.environ.get("ENABLE_LLM", "true").lower() == "true"
LLM_TEMPERATURE = 0.1
LLM_TIMEOUT = 30  # DeepSeek API 超时（秒）

# ========= 搜索配置 =========
SEARCH_LIMIT = 20       # 每页结果数
FUZZY_THRESHOLD = 0.3   # 模糊匹配最低置信度
