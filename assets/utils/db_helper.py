"""
数据库操作工具
"""
import sqlite3
import json
import os


def get_connection(db_path: str) -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def insert_circuit(conn: sqlite3.Connection, record: dict) -> int:
    """插入一条电路摘要记录"""
    sql = """
    INSERT OR IGNORE INTO circuits (
        circuit_no, system_name, circuit_name, endpoint,
        project_phase, source_file, source_sheet,
        system_type, system_category, capacity,
        protection_type, service_type, business_nature,
        route_nature, protection_circuit, protection_endpoint,
        update_date, remark, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(sql, (
        record.get("circuit_no", ""),
        record.get("system_name", ""),
        record.get("circuit_name", ""),
        record.get("endpoint", ""),
        record.get("project_phase", ""),
        record.get("source_file", ""),
        record.get("source_sheet", ""),
        record.get("system_type", ""),
        record.get("system_category", ""),
        record.get("capacity", ""),
        record.get("protection_type", ""),
        record.get("service_type", ""),
        record.get("business_nature", ""),
        record.get("route_nature", ""),
        record.get("protection_circuit", ""),
        record.get("protection_endpoint", ""),
        record.get("update_date", ""),
        record.get("remark", ""),
        record.get("raw_json", "{}"),
    ))
    return conn.total_changes


def insert_hop(conn: sqlite3.Connection, record: dict) -> int:
    """插入一条路由跳段记录"""
    sql = """
    INSERT INTO circuit_hops (
        circuit_no, system_name, hop_order, route_type,
        station_a, station_b, timeslot_id, multiplex_section, device_type,
        a_equipment_id, a_line_slot, a_line_port, a_line_board,
        a_tributary_slot, a_tributary_port, a_tributary_board,
        b_equipment_id, b_line_slot, b_line_port, b_line_board,
        b_tributary_slot, b_tributary_port, b_tributary_board,
        source_file, source_sheet, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(sql, (
        record.get("circuit_no", ""),
        record.get("system_name", ""),
        record.get("hop_order", 0),
        record.get("route_type", ""),
        record.get("station_a", ""),
        record.get("station_b", ""),
        record.get("timeslot_id", ""),
        record.get("multiplex_section", ""),
        record.get("device_type", ""),
        record.get("a_equipment_id", ""),
        record.get("a_line_slot", ""),
        record.get("a_line_port", ""),
        record.get("a_line_board", ""),
        record.get("a_tributary_slot", ""),
        record.get("a_tributary_port", ""),
        record.get("a_tributary_board", ""),
        record.get("b_equipment_id", ""),
        record.get("b_line_slot", ""),
        record.get("b_line_port", ""),
        record.get("b_line_board", ""),
        record.get("b_tributary_slot", ""),
        record.get("b_tributary_port", ""),
        record.get("b_tributary_board", ""),
        record.get("source_file", ""),
        record.get("source_sheet", ""),
        record.get("raw_json", "{}"),
    ))
    return conn.total_changes


def insert_multiplex_section(conn: sqlite3.Connection, record: dict) -> int:
    """插入一条复用段记录"""
    sql = """
    INSERT INTO multiplex_sections (
        project_phase, system_name,
        link_id, province, station, device_type, platform,
        timeslot_id, multiplex_section_name,
        config_phase, use_phase, usage_type, usage_nature,
        terminal_type, rate,
        source_file, source_sheet, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.execute(sql, (
        record.get("project_phase", ""),
        record.get("system_name", ""),
        record.get("link_id", ""),
        record.get("province", ""),
        record.get("station", ""),
        record.get("device_type", ""),
        record.get("platform", ""),
        record.get("timeslot_id", ""),
        record.get("multiplex_section_name", ""),
        record.get("config_phase", ""),
        record.get("use_phase", ""),
        record.get("usage_type", ""),
        record.get("usage_nature", ""),
        record.get("terminal_type", ""),
        record.get("rate", ""),
        record.get("source_file", ""),
        record.get("source_sheet", ""),
        record.get("raw_json", "{}"),
    ))
    return conn.total_changes


def save_meta(conn: sqlite3.Connection, key: str, value: str):
    """保存预处理元信息"""
    conn.execute(
        "INSERT OR REPLACE INTO preprocess_meta (key, value) VALUES (?, ?)",
        (key, value)
    )
