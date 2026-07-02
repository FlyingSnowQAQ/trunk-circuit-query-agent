"""
配置文件 - 移动干线电路查询系统
所有文件路径在此集中管理，可通过环境变量覆盖
"""
import os

# 基础数据目录
BASE_DATA_DIR = os.environ.get(
    "CIRCUIT_DATA_DIR",
    r"D:/常用资料/路由/电路资料/电路查询"
)

# 输出目录
OUTPUT_DIR = os.environ.get(
    "CIRCUIT_OUTPUT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
)

# 1. 汇总Excel文件路径
SUMMARY_EXCEL = os.environ.get(
    "CIRCUIT_SUMMARY_EXCEL",
    os.path.join(
        BASE_DATA_DIR,
        "1-移动干线电路名称汇总（仅工程电路名称汇总集团调度电路不在此列).xlsx"
    )
)

# 2. 光通道路由表目录
ROUTING_TABLE_DIR = os.environ.get(
    "CIRCUIT_ROUTING_DIR",
    os.path.join(BASE_DATA_DIR, "2-光通道路由表")
)

# 3. 具体路由表目录 (补充网元ID/槽位/端口信息)
DETAIL_ROUTING_DIR = os.environ.get(
    "CIRCUIT_DETAIL_DIR",
    os.path.join(BASE_DATA_DIR, "3-具体路由表-包含各厂家具体网元ID槽位端口")
)

# SQLite数据库路径
DB_PATH = os.path.join(OUTPUT_DIR, "circuits.db")

# API服务配置
API_HOST = os.environ.get("CIRCUIT_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("CIRCUIT_API_PORT", "5000"))

# FTS分页默认值
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 日志文件
LOG_FILE = os.path.join(OUTPUT_DIR, "preprocess.log")
