"""
启动移动干线电路查询智能体服务

用法:
    python start_server.py [--port PORT] [--host HOST]

环境变量:
    CIRCUIT_DB_PATH   - 数据库路径
    DEEPSEEK_API_KEY  - DeepSeek API 密钥（可选）
    CIRCUIT_API_PORT  - 服务端口（默认 8000）
"""
import os
import sys
import subprocess

# 确保项目根在 sys.path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 清理冲突环境变量
os.environ.pop("PYTHONHOME", None)

# 启动服务
cmd = [sys.executable, "-m", "api.server"]
if len(sys.argv) > 1:
    cmd.extend(sys.argv[1:])

print("=" * 50)
print("  移动干线电路查询智能体 - 启动中...")
print("=" * 50)
print(f"  Python: {sys.executable}")
print(f"  项目:   {ROOT}")
print(f"  端口:   {os.environ.get('CIRCUIT_API_PORT', '8000')}")
print("=" * 50)

subprocess.run(cmd, cwd=ROOT)
