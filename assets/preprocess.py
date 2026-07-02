"""
预处理主脚本

1. 解析汇总Excel的15个sheet -> circuits表
2. 解析路由表目录 -> circuit_hops / multiplex_sections表
3. 构建FTS全文索引
4. 输出数据校验报告
"""
import os
import sys
import time
import json

# 确保能导入项目包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SUMMARY_EXCEL, ROUTING_TABLE_DIR, DB_PATH, OUTPUT_DIR, LOG_FILE
from parsers.schema import create_schema
from parsers.summary_parser import parse_summary_excel
from parsers.route_parser import batch_parse_routing_dir
from utils.db_helper import get_connection, insert_circuit, insert_hop, insert_multiplex_section, save_meta
from utils.logger import setup_logger


def main():
    # 确保输出目录存在（必须在 logger 之前，因为 logger 要写日志到该目录）
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger = setup_logger(LOG_FILE)

    start_time = time.time()
    logger.info("=" * 60)
    logger.info("移动干线电路查询系统 - 数据预处理开始")
    logger.info("=" * 60)

    # Step 1: 创建数据库Schema
    logger.info("[1/5] 创建数据库表结构...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logger.info(f"  删除旧数据库: {DB_PATH}")
    create_schema(DB_PATH)
    logger.info(f"  数据库创建完成: {DB_PATH}")

    conn = get_connection(DB_PATH)

    # Step 2: 解析汇总Excel
    logger.info("[2/5] 解析汇总Excel...")
    logger.info(f"  文件: {SUMMARY_EXCEL}")
    try:
        summary_records = parse_summary_excel(SUMMARY_EXCEL)
        logger.info(f"  解析完成，共 {len(summary_records)} 条记录")

        # 批量入库 - 每500条提交一次
        batch_size = 500
        inserted = 0
        for i in range(0, len(summary_records), batch_size):
            batch = summary_records[i:i + batch_size]
            for rec in batch:
                insert_circuit(conn, rec)
            conn.commit()
            inserted += len(batch)
            if (i + batch_size) % 5000 == 0 or i + batch_size >= len(summary_records):
                logger.info(f"  已入库 {inserted}/{len(summary_records)} 条")
        logger.info(f"  电路摘要入库完成: {inserted} 条")
    except Exception as e:
        logger.error(f"  解析汇总Excel失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        summary_records = []

    # Step 3: 解析路由表
    logger.info("[3/5] 解析路由表目录...")
    logger.info(f"  目录: {ROUTING_TABLE_DIR}")
    try:
        route_results = batch_parse_routing_dir(ROUTING_TABLE_DIR)
        total_hop = 0
        total_mux = 0
        total_circuit = 0
        total_errors = 0

        for phase, records in route_results.items():
            if phase == "_error":
                logger.error(f"  路由表目录错误: {records}")
                continue
            if phase == "_unmatched":
                logger.warning(f"  未匹配文件: {records}")
                continue

            for rec in records:
                if "_error" in rec:
                    logger.warning(f"  [{phase}] 解析失败: {rec['_error']}")
                    total_errors += 1
                    continue

                table_type = rec.pop("_table", "circuits")
                try:
                    if table_type == "circuit_hops":
                        insert_hop(conn, rec)
                        total_hop += 1
                    elif table_type == "multiplex_sections":
                        insert_multiplex_section(conn, rec)
                        total_mux += 1
                    else:
                        insert_circuit(conn, rec)
                        total_circuit += 1
                except Exception as e:
                    logger.warning(f"  入库失败 [{phase}]: {e}")
                    total_errors += 1

            conn.commit()
            logger.info(f"  [{phase}] 路由表解析完成: "
                        f"跳段={total_hop}, 复用段={total_mux}, 电路={total_circuit}, 错误={total_errors}")
    except Exception as e:
        logger.error(f"  解析路由表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

    # Step 4: 重建FTS索引（补充触发器中可能遗漏的行）
    logger.info("[4/5] 重建全文搜索索引...")
    try:
        conn.execute("""
            INSERT INTO circuits_fts(circuits_fts, rowid, circuit_no, system_name, circuit_name, endpoint)
            SELECT 'delete', id, circuit_no, system_name, circuit_name, endpoint FROM circuits
        """)
        conn.execute("""
            INSERT INTO circuits_fts(rowid, circuit_no, system_name, circuit_name, endpoint)
            SELECT id, circuit_no, system_name, circuit_name, endpoint FROM circuits
        """)
        conn.commit()
        logger.info("  FTS索引重建完成")
    except Exception as e:
        logger.warning(f"  FTS索引重建警告: {e}")

    # Step 5: 数据校验
    logger.info("[5/5] 数据统计报告...")
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM circuits")
        circuit_count = cursor.fetchone()["cnt"]
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM circuit_hops")
        hop_count = cursor.fetchone()["cnt"]
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM multiplex_sections")
        mux_count = cursor.fetchone()["cnt"]

        # 按建设期统计
        cursor = conn.execute(
            "SELECT project_phase, COUNT(*) as cnt FROM circuits "
            "WHERE project_phase != '' GROUP BY project_phase ORDER BY cnt DESC"
        )
        phase_stats = {row["project_phase"]: row["cnt"] for row in cursor.fetchall()}

        # 系统名 TOP 20
        cursor = conn.execute(
            "SELECT system_name, COUNT(*) as cnt FROM circuits "
            "WHERE system_name != '' GROUP BY system_name "
            "ORDER BY cnt DESC LIMIT 20"
        )
        top_systems = [dict(row) for row in cursor.fetchall()]

        logger.info(f"  ┌────────────────────────────┬──────────┐")
        logger.info(f"  │ 表名                       │ 记录数   │")
        logger.info(f"  ├────────────────────────────┼──────────┤")
        logger.info(f"  │ circuits (电路摘要)         │ {circuit_count:>8} │")
        logger.info(f"  │ circuit_hops (路由跳段)     │ {hop_count:>8} │")
        logger.info(f"  │ multiplex_sections (复用段) │ {mux_count:>8} │")
        logger.info(f"  └────────────────────────────┴──────────┘")
        logger.info(f"  按建设期分布: {json.dumps(phase_stats, ensure_ascii=False)}")
        logger.info(f"  前20系统名: {json.dumps(top_systems[:5], ensure_ascii=False)}...")

        # 保存元信息
        save_meta(conn, "circuits_count", str(circuit_count))
        save_meta(conn, "hops_count", str(hop_count))
        save_meta(conn, "mux_count", str(mux_count))
        save_meta(conn, "preprocess_time", time.strftime("%Y-%m-%d %H:%M:%S"))
        save_meta(conn, "duration_seconds", str(int(time.time() - start_time)))
        conn.commit()

    except Exception as e:
        logger.error(f"  数据统计失败: {e}")

    conn.close()

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"预处理完成！耗时 {elapsed:.1f} 秒")
    logger.info(f"数据库文件: {DB_PATH}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
