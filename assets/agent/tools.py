"""
智能体工具层

提供三个核心工具函数，用于查询移动干线电路数据：
1. lookup_phase   — 根据系统名查询所属工程期数
2. query_routing  — 查询指定电路的路由跳段详情
3. fuzzy_match   — LLM辅助模糊匹配系统名

所有工具直接读取已有的 circuits.db，不修改任何数据。
"""
import sqlite3
import re
import json
from typing import Optional

from config import DB_PATH, SEARCH_LIMIT


def _get_conn() -> sqlite3.Connection:
    """获取只读数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON;")
    return conn


def _identify_vendor(device_type: str) -> str:
    """根据设备类型识别设备厂家"""
    if not device_type or device_type.strip() in ("", "0"):
        return ""
    dt = device_type.upper().strip()
    # 烽火
    if dt.startswith("FONST"):
        return "烽火"
    # 华为
    if dt.startswith("OSN") or dt.startswith("OPTIX"):
        return "华为"
    # 中兴
    if dt.startswith("ZX"):
        return "中兴"
    # 诺基亚
    if dt.startswith("1830PSS"):
        return "诺基亚"
    return ""


def _split_keywords(text: str) -> list[str]:
    """将系统名拆分为关键词列表（用于多条件 LIKE 匹配）"""
    # 去除常见分隔符
    parts = re.split(r'[ \-_／/（）()（）【】\[\]&＋+，,]', text)
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def lookup_phase(system_name: str) -> dict:
    """
    工具1：根据传输系统名查询其所属工程期数

    参数:
        system_name: 传输系统名（如 "北京-上海39系统"）

    返回:
        {
            "found": bool,
            "phase": str 或 None,
            "match_type": str,       # "精确匹配" | "模糊匹配" | "未匹配"
            "circuits": list[dict],  # 匹配到的电路列表
        }
    """
    conn = _get_conn()
    results = {"found": False, "phase": None, "match_type": "未匹配", "circuits": []}

    try:
        # === 策略1: 精确匹配（同时查系统名和电路名） ===
        cursor = conn.execute(
            "SELECT DISTINCT circuit_no, system_name, circuit_name, endpoint, "
            "       project_phase, system_type, capacity "
            "FROM circuits "
            "WHERE system_name = ? OR circuit_name = ? "
            "ORDER BY project_phase "
            "LIMIT ?",
            (system_name, system_name, SEARCH_LIMIT),
        )
        rows = cursor.fetchall()

        # === 策略2: 关键词分段 LIKE 匹配 ===
        if not rows:
            keywords = _split_keywords(system_name)
            if len(keywords) >= 2:
                conditions = " AND ".join(["system_name LIKE ?"] * len(keywords))
                params = [f"%{kw}%" for kw in keywords]
                sql = (
                    f"SELECT DISTINCT circuit_no, system_name, circuit_name, endpoint, "
                    f"       project_phase, system_type, capacity "
                    f"FROM circuits "
                    f"WHERE {conditions} "
                    f"ORDER BY project_phase LIMIT ?"
                )
                cursor = conn.execute(sql, params + [SEARCH_LIMIT])
                rows = cursor.fetchall()

        # === 策略3: 单 LIKE 模糊匹配 ===
        if not rows:
            cursor = conn.execute(
                "SELECT DISTINCT circuit_no, system_name, circuit_name, endpoint, "
                "       project_phase, system_type, capacity "
                "FROM circuits "
                "WHERE system_name LIKE ? "
                "ORDER BY project_phase "
                "LIMIT ?",
                (f"%{system_name}%", SEARCH_LIMIT),
            )
            rows = cursor.fetchall()

        # === 策略4: 直接作为 circuit_name 搜索（输入可能是电路名而非系统名） ===
        if not rows:
            cursor = conn.execute(
                "SELECT DISTINCT circuit_no, system_name, circuit_name, endpoint, "
                "       project_phase, system_type, capacity "
                "FROM circuits "
                "WHERE circuit_name = ? "
                "ORDER BY project_phase "
                "LIMIT ?",
                (system_name, SEARCH_LIMIT),
            )
            rows = cursor.fetchall()

        if rows:
            # 提取期数（取第一条匹配的）
            phases = set(r["project_phase"] for r in rows if r["project_phase"])
            results["found"] = True
            results["phase"] = sorted(phases)[0] if phases else None
            results["match_type"] = "精确匹配" if len(rows) == 1 and rows[0]["system_name"] == system_name else "模糊匹配"
            results["circuits"] = [dict(r) for r in rows]

    finally:
        conn.close()

    return results


def query_routing(circuit_no: Optional[str] = None,
                  system_name: Optional[str] = None,
                  circuit_name: Optional[str] = None,
                  project_phase: Optional[str] = None) -> dict:
    """
    工具2：查询指定电路的路由跳段详情 — 四级匹配策略

    匹配优先级：
    1. circuit_name + project_phase 双重匹配（最精准）
    2. circuit_name 精确匹配
    3. circuit_no 精确匹配
    4. system_name LIKE 模糊匹配（兜底）

    返回 ALL 匹配行（而非只取第一条）。

    参数:
        circuit_no:    电路编号
        system_name:   系统名称
        circuit_name:  电路名称
        project_phase: 工程期数（配合 circuit_name 使用）

    返回:
        {
            "has_hops": bool,
            "total_hops": int,
            "has_device_detail": bool,
            "match_type": str,    # 标记匹配方式
            "hops": list[dict],   # 返回 ALL 行
        }
    """
    conn = _get_conn()
    result = {
        "has_hops": False, "total_hops": 0, "has_device_detail": False,
        "match_type": "", "hops": [],
    }
    # 全部字段列表（含 project_phase 和端口板卡字段）
    FIELDS = (
        "hop_order, station_a, station_b, timeslot_id, "
        "multiplex_section, device_type, route_type, circuit_name, "
        "project_phase, "
        "a_equipment_id, a_line_slot, a_line_port, a_line_board, "
        "a_tributary_slot, a_tributary_port, a_tributary_board, "
        "b_equipment_id, b_line_slot, b_line_port, b_line_board, "
        "b_tributary_slot, b_tributary_port, b_tributary_board, "
        "board_type_a, board_type_b"
    )

    try:
        rows = []

        # ─── 等级1: circuit_name + project_phase 双重匹配（最精准） ───
        if not rows and circuit_name and project_phase:
            cursor = conn.execute(
                f"SELECT {FIELDS} FROM circuit_hops "
                "WHERE circuit_name = ? AND project_phase = ? "
                "ORDER BY hop_order",
                (circuit_name, project_phase),
            )
            rows = cursor.fetchall()
            if rows:
                result["match_type"] = f"电路名称+期数匹配（{circuit_name}@{project_phase}）"

        # ─── 等级2: circuit_name 匹配（处理顺序不一致问题） ───
        if not rows and circuit_name:
            # 先试精确匹配
            cursor = conn.execute(
                f"SELECT {FIELDS} FROM circuit_hops "
                "WHERE circuit_name = ? ORDER BY hop_order",
                (circuit_name,),
            )
            rows = cursor.fetchall()

            # 精确匹配不到时，拆成关键词 LIKE 匹配
            if not rows:
                keywords = _split_keywords(circuit_name)
                if len(keywords) >= 2:
                    conditions = " AND ".join(["circuit_name LIKE ?"] * len(keywords))
                    params = [f"%{kw}%" for kw in keywords]
                    cursor = conn.execute(
                        f"SELECT {FIELDS} FROM circuit_hops "
                        f"WHERE {conditions} ORDER BY hop_order",
                        params,
                    )
                    rows = cursor.fetchall()

            if rows:
                result["match_type"] = f"电路名称匹配（{circuit_name}）"

        # ─── 等级3: circuit_no 精确匹配 ───
        if not rows and circuit_no:
            cursor = conn.execute(
                f"SELECT {FIELDS} FROM circuit_hops "
                "WHERE circuit_no = ? ORDER BY hop_order",
                (circuit_no,),
            )
            rows = cursor.fetchall()
            if rows:
                result["match_type"] = "电路编号匹配"

        # ─── 等级4: system_name LIKE 模糊匹配 ───
        if not rows and system_name:
            cursor = conn.execute(
                f"SELECT {FIELDS} FROM circuit_hops "
                "WHERE system_name LIKE ? ORDER BY hop_order",
                (f"%{system_name}%",),
            )
            rows = cursor.fetchall()
            if rows:
                result["match_type"] = "系统名模糊匹配"

        # 构造 hops 结果（返回 ALL 行）
        if rows:
            result["has_hops"] = True
            result["total_hops"] = len(rows)
            # 检查是否有设备级端口信息（含板卡字段）
            has_device = any(
                r["a_equipment_id"] or r["a_line_slot"] or r["a_line_port"]
                or r["b_equipment_id"] or r["b_line_slot"] or r["b_line_port"]
                or r["a_line_board"] or r["b_line_board"]
                or r["a_tributary_slot"] or r["b_tributary_slot"]
                for r in rows
            )
            result["has_device_detail"] = has_device
            hops = [dict(r) for r in rows]
            # 注入设备厂家信息
            for hop in hops:
                hop["vendor"] = _identify_vendor(hop.get("device_type", ""))
            result["hops"] = hops

    finally:
        conn.close()

    return result


def fuzzy_match(system_name: str, llm_client=None) -> str:
    """
    工具3：LLM辅助模糊匹配系统名

    当 SQL 搜索无结果时，调用 LLM 帮助理解用户意图并纠正系统名。
    如果 LLM 不可用，返回原始名称。

    参数:
        system_name: 用户输入的系统名
        llm_client:  LLM客户端实例（可选）

    返回:
        纠正后的系统名（或原始名称）
    """
    if not llm_client:
        return system_name

    prompt = f"""你是中国移动干线电路查询系统的名称纠错模块。

用户输入了一个传输系统名："{system_name}"

但数据库中未找到该名称。请尝试以下纠正策略：
1. 移除可能的错别字或多余字符
2. 补全常见的系统名格式（如"北京-上海39系统"格式）
3. 解析缩写或变体（如"京沪39"→"北京-上海39系统"）

请直接输出你认为最可能的正确系统名，不要有任何解释和额外文字。
只输出名称本身。"""

    try:
        corrected = llm_client._call_llm(prompt, max_tokens=64, temperature=0.1)
        corrected = corrected.strip().strip('"\'「」')
        if corrected and len(corrected) >= 4:
            return corrected
    except Exception:
        pass

    return system_name


def search_circuits(keyword: str, page: int = 1, page_size: int = 20) -> dict:
    """
    快捷搜索电路（跳过智能体），直接对应旧系统 search 端点

    返回:
        { "total": int, "page": int, "page_size": int, "results": list[dict] }
    """
    conn = _get_conn()
    try:
        offset = (page - 1) * page_size
        # 计数
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM circuits WHERE "
            "circuit_no LIKE ? OR system_name LIKE ? OR circuit_name LIKE ? OR endpoint LIKE ?",
            (f"%{keyword}%",) * 4,
        ).fetchone()
        total = count_row["cnt"] if count_row else 0

        # 查数据
        cursor = conn.execute(
            "SELECT circuit_no, system_name, circuit_name, endpoint, "
            "       project_phase, system_type, capacity "
            "FROM circuits "
            "WHERE circuit_no LIKE ? OR system_name LIKE ? "
            "   OR circuit_name LIKE ? OR endpoint LIKE ? "
            "ORDER BY project_phase "
            "LIMIT ? OFFSET ?",
            (f"%{keyword}%",) * 4 + (page_size, offset),
        )
        results = [dict(r) for r in cursor.fetchall()]

        # 标记是否有详情（优先按 circuit_no，其次按 circuit_name）
        for r in results:
            hop = conn.execute(
                "SELECT COUNT(*) as cnt FROM circuit_hops WHERE circuit_no = ?",
                (r["circuit_no"],),
            ).fetchone()
            has_detail = (hop["cnt"] if hop else 0) > 0
            if not has_detail and r.get("circuit_name"):
                hop = conn.execute(
                    "SELECT COUNT(*) as cnt FROM circuit_hops WHERE circuit_name = ?",
                    (r["circuit_name"],),
                ).fetchone()
                has_detail = (hop["cnt"] if hop else 0) > 0
            r["has_detail"] = has_detail

    finally:
        conn.close()

    return {"total": total, "page": page, "page_size": page_size, "results": results}


def get_db_stats() -> dict:
    """返回数据库统计信息"""
    conn = _get_conn()
    try:
        circuit_count = conn.execute("SELECT COUNT(*) as c FROM circuits").fetchone()["c"]
        hop_count = conn.execute("SELECT COUNT(*) as c FROM circuit_hops").fetchone()["c"]
        mux_count = conn.execute("SELECT COUNT(*) as c FROM multiplex_sections").fetchone()["c"]

        phases = conn.execute(
            "SELECT project_phase, COUNT(*) as cnt FROM circuits "
            "WHERE project_phase != '' GROUP BY project_phase ORDER BY cnt DESC"
        ).fetchall()

        return {
            "circuits": circuit_count,
            "hops": hop_count,
            "multiplex_sections": mux_count,
            "db_size_mb": round(os.path.getsize(DB_PATH) / (1024 * 1024), 1) if os.path.exists(DB_PATH) else 0,
            "phases": {r["project_phase"]: r["cnt"] for r in phases},
        }
    finally:
        conn.close()


import os  # noqa: E402 — 用于 get_db_stats 中的 os.path.getsize
