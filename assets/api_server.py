"""
Flask API 服务 - 移动干线电路查询

提供以下接口:
- GET /api/health          - 健康检查
- GET /api/phases          - 获取所有建设期
- GET /api/circuits/search - 搜索电路摘要 (按系统名/电路名/电路编号)
- GET /api/circuits/detail - 获取电路路由详情
"""
import sys
import os
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_PATH, API_HOST, API_PORT, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def get_db():
    """获取数据库连接"""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


# ==================== 健康检查 ====================

@app.route("/api/health", methods=["GET"])
def health():
    """健康检查接口"""
    if not os.path.exists(DB_PATH):
        return jsonify({
            "code": 1,
            "message": "数据库不存在，请先运行 preprocess.py",
            "data": {
                "status": "error",
                "db_exists": False,
                "db_path": DB_PATH
            }
        })

    db_size = os.path.getsize(DB_PATH)
    conn = get_db()
    if conn is None:
        return jsonify({"code": 1, "message": "数据库连接失败"})

    try:
        cursor = conn.execute("SELECT value FROM preprocess_meta WHERE key='circuits_count'")
        row = cursor.fetchone()
        circuit_count = int(row["value"]) if row else 0
        conn.close()
    except:
        circuit_count = 0
        conn.close()

    return jsonify({
        "code": 0,
        "data": {
            "status": "ok",
            "db_size_mb": round(db_size / 1024 / 1024, 1),
            "circuits_count": circuit_count,
            "db_path": DB_PATH
        }
    })


# ==================== 建设期列表 ====================

@app.route("/api/phases", methods=["GET"])
def phases():
    """获取所有建设期列表"""
    conn = get_db()
    if conn is None:
        return jsonify({"code": 1, "message": "数据库不存在"})

    try:
        cursor = conn.execute(
            "SELECT DISTINCT project_phase FROM circuits "
            "WHERE project_phase != '' ORDER BY project_phase"
        )
        phase_list = [row["project_phase"] for row in cursor.fetchall()]
        conn.close()
        return jsonify({"code": 0, "data": {"phases": phase_list}})
    except Exception as e:
        conn.close()
        return jsonify({"code": 1, "message": str(e)})


# ==================== 电路搜索（摘要） ====================

@app.route("/api/circuits/search", methods=["GET"])
def search_circuits():
    """
    搜索电路摘要
    
    参数:
        q: 搜索关键词（系统名/电路名/电路编号）
        page: 页码 (默认1)
        page_size: 每页数量 (默认20, 最大100)
        phase: 按建设期过滤 (可选)
    """
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", DEFAULT_PAGE_SIZE, type=int)
    phase_filter = request.args.get("phase", "").strip()

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE

    if not query:
        return jsonify({"code": 1, "message": "请提供搜索关键词 q"})

    conn = get_db()
    if conn is None:
        return jsonify({"code": 1, "message": "数据库不存在"})

    try:
        total, results = _execute_search(conn, query, page, page_size, phase_filter)
        conn.close()

        # 清洗输出字段
        for rec in results:
            rec.pop("_from_fuzzy", None)
            rec.pop("raw_json", None)
            rec.pop("id", None)

        return jsonify({
            "code": 0,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": max(1, (total + page_size - 1) // page_size),
                "results": results
            }
        })
    except Exception as e:
        conn.close()
        return jsonify({"code": 1, "message": str(e)})


def _execute_search(conn, query: str, page: int, page_size: int, phase_filter: str) -> tuple:
    """
    执行搜索
    
    搜索策略: 
    1. 先用FTS全文搜索（对短词效果好）
    2. 再用LIKE模糊搜索（对长词/中文效果好）
    3. 合并结果去重
    """
    # 预处理查询词
    query_clean = query.strip().replace(" ", "")

    # 构建搜索条件
    # 使用 LIKE 模糊搜索（对中文友好）作为主要搜索方式
    like_conditions = []
    like_params = []

    # 拆分查询词，每个词作为一个独立LIKE条件
    keywords = query.strip().split()
    for kw in keywords:
        if kw.strip():
            like_conditions.append(
                "(c.system_name LIKE ? OR c.circuit_name LIKE ? OR c.circuit_no LIKE ? OR c.endpoint LIKE ?)"
            )
            p = f"%{kw.strip()}%"
            like_params.extend([p, p, p, p])

    if not like_conditions:
        return 0, []

    like_where = " AND ".join(like_conditions)

    # 按建设期过滤
    phase_where = ""
    if phase_filter:
        phase_where = "AND c.project_phase = ?"
        like_params.append(phase_filter)

    # 查询总数
    sql_count = f"""
        SELECT COUNT(*) as cnt
        FROM circuits c
        WHERE {like_where} {phase_where}
    """
    cursor = conn.execute(sql_count, like_params)
    total = cursor.fetchone()["cnt"]

    # 查询数据
    offset = (page - 1) * page_size
    sql_data = f"""
        SELECT c.*
        FROM circuits c
        WHERE {like_where} {phase_where}
        ORDER BY c.id
        LIMIT ? OFFSET ?
    """
    data_params = like_params + [page_size, offset]

    cursor = conn.execute(sql_data, data_params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        rec = dict(row)
        # 移除内部字段
        rec.pop("raw_json", None)
        rec.pop("id", None)
        # 标记是否有详细信息
        rec["has_detail"] = _check_has_detail_by_system(conn, rec.get("circuit_no", ""), rec.get("system_name", ""))
        rec["has_device_detail"] = _check_has_device_detail(conn, rec.get("circuit_no", ""))
        results.append(rec)

    # 如果主搜索结果不足，补充模糊搜索
    if total < 20 and len(query) > 1:
        fuzzy_results = _fuzzy_search_fallback(conn, query, phase_filter, limit=50)
        # 去重
        existing_ids = {(r.get("circuit_no", ""), r.get("system_name", "")) for r in results}
        for rec in fuzzy_results:
            key = (rec.get("circuit_no", ""), rec.get("system_name", ""))
            if key not in existing_ids:
                results.append(rec)
                total += 1

    return total, results


def _fuzzy_search_fallback(conn, query: str, phase_filter: str, limit: int) -> list:
    """FTS搜索不到时的模糊匹配备用方案"""
    conditions = []
    params = []

    like_pattern = f"%{query}%"
    conditions.append("(system_name LIKE ? OR circuit_name LIKE ? OR circuit_no LIKE ?)")
    params.extend([like_pattern, like_pattern, like_pattern])

    if phase_filter:
        conditions.append("project_phase = ?")
        params.append(phase_filter)

    where_clause = " AND ".join(conditions)
    sql = f"SELECT * FROM circuits WHERE {where_clause} LIMIT ?"
    params.append(limit)

    try:
        cursor = conn.execute(sql, params)
        results = []
        for row in cursor.fetchall():
            rec = dict(row)
            rec.pop("raw_json", None)
            rec.pop("id", None)
            rec["has_detail"] = _check_has_detail_by_system(conn, rec.get("circuit_no", ""), rec.get("system_name", ""))
            rec["has_device_detail"] = _check_has_device_detail(conn, rec.get("circuit_no", ""))
            results.append(rec)
        return results
    except Exception:
        return []


def _check_has_detail_by_system(conn, circuit_no: str, system_name: str) -> bool:
    """检查是否有路由详情（优先按circuit_no，其次按system_name LIKE）"""
    if circuit_no:
        cursor = conn.execute(
            "SELECT COUNT(*) as cnt FROM circuit_hops WHERE circuit_no = ?",
            (circuit_no,)
        )
        cnt = cursor.fetchone()["cnt"]
        if cnt > 0:
            return True

    if system_name:
        # 尝试精确匹配
        cursor = conn.execute(
            "SELECT COUNT(*) as cnt FROM circuit_hops WHERE system_name = ?",
            (system_name,)
        )
        cnt = cursor.fetchone()["cnt"]
        if cnt > 0:
            return True
        # 尝试部分匹配（处理命名差异）
        parts = system_name.replace("系统", "").replace("W-", "-").replace("-W", "-").split("-")
        for part in parts:
            if len(part) >= 2:
                cursor = conn.execute(
                    "SELECT COUNT(*) as cnt FROM circuit_hops WHERE system_name LIKE ?",
                    (f"%{part}%",)
                )
                cnt = cursor.fetchone()["cnt"]
                if cnt > 10:
                    return True

    return False


def _check_has_device_detail(conn, circuit_no: str) -> bool:
    """检查是否有设备级详情"""
    if not circuit_no:
        return False
    cursor = conn.execute(
        "SELECT COUNT(*) as cnt FROM circuit_hops "
        "WHERE circuit_no = ? AND (a_equipment_id != '' OR a_line_slot != '')",
        (circuit_no,)
    )
    row = cursor.fetchone()
    return row["cnt"] > 0


# ==================== 电路详情 ====================

@app.route("/api/circuits/detail", methods=["GET"])
def circuit_detail():
    """
    获取电路路由详情

    参数:
        circuit_no: 电路编号 (必填)
        system_name: 系统名称 (可选，精确定位)
    """
    circuit_no = request.args.get("circuit_no", "").strip()
    system_name = request.args.get("system_name", "").strip()

    if not circuit_no and not system_name:
        return jsonify({"code": 1, "message": "请提供 circuit_no 或 system_name"})

    conn = get_db()
    if conn is None:
        return jsonify({"code": 1, "message": "数据库不存在"})

    try:
        # 获取电路基本信息
        if circuit_no and system_name:
            cursor = conn.execute(
                "SELECT * FROM circuits WHERE circuit_no = ? AND system_name = ?",
                (circuit_no, system_name)
            )
        elif circuit_no:
            cursor = conn.execute(
                "SELECT * FROM circuits WHERE circuit_no = ? LIMIT 5",
                (circuit_no,)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM circuits WHERE system_name LIKE ? LIMIT 5",
                (f"%{system_name}%",)
            )

        circuit_info = [dict(row) for row in cursor.fetchall()]
        for rec in circuit_info:
            rec.pop("raw_json", None)
            rec.pop("id", None)

        if not circuit_info and not system_name:
            conn.close()
            return jsonify({"code": 1, "message": "未找到该电路"})

        # 获取路由跳段：优先 circuit_no，其次 system_name
        hops = []
        if circuit_no:
            cursor = conn.execute(
                "SELECT * FROM circuit_hops WHERE circuit_no = ? ORDER BY hop_order",
                (circuit_no,)
            )
            hops = [dict(row) for row in cursor.fetchall()]

        if not hops and system_name:
            # 精确匹配
            cursor = conn.execute(
                "SELECT * FROM circuit_hops WHERE system_name = ? ORDER BY hop_order",
                (system_name,)
            )
            hops = [dict(row) for row in cursor.fetchall()]

        if not hops and system_name:
            # 模糊匹配（处理命名差异，如 "北京-上海39系统" vs "北京-上海W-139"）
            parts = system_name.replace("系统", "").replace("W", "").split("-")
            for part in parts:
                if len(part) >= 2:
                    cursor = conn.execute(
                        "SELECT * FROM circuit_hops WHERE system_name LIKE ? ORDER BY hop_order LIMIT 100",
                        (f"%{part}%",)
                    )
                    hops = [dict(row) for row in cursor.fetchall()]
                    if hops:
                        break

        for rec in hops:
            rec.pop("raw_json", None)
            rec.pop("id", None)

        # 获取复用段信息（multiplex_sections 表无 circuit_no 列，直接用 system_name 查询）
        mux_sections = []
        if system_name:
            cursor = conn.execute(
                "SELECT * FROM multiplex_sections WHERE system_name LIKE ? LIMIT 50",
                (f"%{system_name}%",)
            )
            mux_sections = [dict(row) for row in cursor.fetchall()]
        elif circuit_info:
            # 从电路信息中取系统名
            sn = circuit_info[0].get("system_name", "")
            if sn:
                cursor = conn.execute(
                    "SELECT * FROM multiplex_sections WHERE system_name LIKE ? LIMIT 50",
                    (f"%{sn}%",)
                )
                mux_sections = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            "code": 0,
            "data": {
                "circuit_info": circuit_info,
                "hops": hops,
                "multiplex_sections": mux_sections,
                "has_hops": len(hops) > 0,
                "has_mux_sections": len(mux_sections) > 0,
                "has_device_detail": any(
                    h.get("a_equipment_id") or h.get("a_line_slot")
                    for h in hops
                )
            }
        })
    except Exception as e:
        conn.close()
        return jsonify({"code": 1, "message": str(e)})


# ==================== 智能搜索 ====================

@app.route("/api/circuits/intelligent", methods=["GET"])
def intelligent_search():
    """
    智能搜索：自动识别查询类型并按最佳方式搜索
    
    参数:
        q: 任意搜索关键词
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"code": 1, "message": "请提供搜索关键词"})

    conn = get_db()
    if conn is None:
        return jsonify({"code": 1, "message": "数据库不存在"})

    try:
        # 同时用多种方式搜索
        total, fts_results = _execute_search(conn, query, 1, 30, "")
        fuzzy_results = _fuzzy_search_fallback(conn, query, "", limit=30)

        # 合并去重
        seen = set()
        combined = []
        for rec in fts_results + fuzzy_results:
            key = (rec.get("circuit_no", ""), rec.get("system_name", ""))
            if key not in seen:
                seen.add(key)
                combined.append(rec)

        conn.close()

        return jsonify({
            "code": 0,
            "data": {
                "total": len(combined),
                "results": combined[:50],  # 最多50条
                "search_method": "intelligent"
            }
        })
    except Exception as e:
        conn.close()
        return jsonify({"code": 1, "message": str(e)})


# ==================== 启动 ====================

if __name__ == "__main__":
    print(f"启动 API 服务...")
    print(f"  数据库: {DB_PATH}")
    print(f"  监听: {API_HOST}:{API_PORT}")
    print(f"  接口列表:")
    print(f"    GET /api/health")
    print(f"    GET /api/phases")
    print(f"    GET /api/circuits/search?q=北京-上海39系统")
    print(f"    GET /api/circuits/detail?circuit_no=4950")
    print(f"    GET /api/circuits/intelligent?q=北京-上海39")
    print()

    app.run(host=API_HOST, port=API_PORT, debug=False)
