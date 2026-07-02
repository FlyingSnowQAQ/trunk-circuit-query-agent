"""
数据库迁移脚本：给 circuit_hops 添加 circuit_name 列并回填数据

运行方式：
    PYTHONHOME="" PYTHONPATH="" python migrate_db.py

注意：需要先确保 circuits.db 文件存在且权可读可写
"""
import os
import sys

# 确保项目根目录在 sys.path 中
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import sqlite3
from config import DB_PATH


def get_stats(conn):
    """获取迁移前后统计数据"""
    total = conn.execute("SELECT COUNT(*) as c FROM circuit_hops").fetchone()["c"]
    filled = conn.execute(
        "SELECT COUNT(*) as c FROM circuit_hops WHERE circuit_name IS NOT NULL AND circuit_name != ''"
    ).fetchone()["c"]
    empty = total - filled
    return total, filled, empty


def migrate():
    print("=" * 60)
    print("  电路路由拼接修复 — 数据库迁移")
    print("=" * 60)
    print()

    print(f"  数据库路径: {DB_PATH}")
    print(f"  文件存在: {os.path.exists(DB_PATH)}")
    print()

    if not os.path.exists(DB_PATH):
        print("[✗] 数据库文件不存在！请先运行 circuit-query-system 的 preprocess.py")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 检查是否已迁移
    cursor = conn.execute("PRAGMA table_info(circuit_hops)")
    columns = {row["name"] for row in cursor.fetchall()}

    if "circuit_name" in columns:
        total, filled, empty = get_stats(conn)
        print(f"[跳过] circuit_name 列已存在")
        print(f"       总数: {total} | 已填充: {filled} | 空值: {empty}")
        conn.close()
        return

    # Step 1: 添加列
    print("[1/4] 添加 circuit_name 列...")
    conn.execute("ALTER TABLE circuit_hops ADD COLUMN circuit_name TEXT")

    # Step 2: 创建索引
    print("[2/4] 创建索引 idx_hops_circuit_name...")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hops_circuit_name ON circuit_hops(circuit_name)")
    conn.commit()

    # Step 3: 按 circuit_no 回填
    print("[3/4] 按 circuit_no 回填 circuit_name...")
    conn.execute("""
        UPDATE circuit_hops
        SET circuit_name = (
            SELECT c.circuit_name
            FROM circuits c
            WHERE c.circuit_no = circuit_hops.circuit_no
            LIMIT 1
        )
    """)
    conn.commit()

    before_total, before_filled, before_empty = get_stats(conn)
    print(f"       按 circuit_no 匹配后: 已填充 {before_filled} / {before_total}")

    # Step 4: 按 system_name 回填未匹配项
    print("[4/4] 按 system_name 回填未匹配行...")
    conn.execute("""
        UPDATE circuit_hops
        SET circuit_name = (
            SELECT c.circuit_name
            FROM circuits c
            WHERE c.system_name = circuit_hops.system_name
            LIMIT 1
        )
        WHERE circuit_name IS NULL OR circuit_name = ''
    """)
    conn.commit()

    total, filled, empty = get_stats(conn)
    print(f"       按 system_name 补充后: 已填充 {filled} / {total} (新增 {filled - before_filled})")

    if empty > 0:
        print(f"[!] 警告: 仍有 {empty} 条 circuit_hops 记录未能匹配到 circuit_name")
        print(f"    这些记录可能来自 circuits 表中未收录的电路")
        print(f"    可通过查看 raw_json 字段追溯原始数据")

    conn.close()
    print()
    print("[完成] 数据库迁移成功！")
    print(f"       circuit_hops 共 {total} 条，已回填 {filled} 条 circuit_name")
    print()


if __name__ == "__main__":
    migrate()
