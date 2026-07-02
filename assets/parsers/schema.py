"""
数据库Schema定义
"""
import sqlite3

SCHEMA_SQL = """
-- 核心表: 电路摘要（从汇总Excel解析）
CREATE TABLE IF NOT EXISTS circuits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 查询关键字段
    circuit_no TEXT,              -- 电路编号/电路号 (统一化处理)
    system_name TEXT,             -- 系统名称 (如 "北京-上海W-3")
    circuit_name TEXT,            -- 电路名称 (如 "北京CR1-上海CR1")
    endpoint TEXT,                -- 终端点 (如 "北京菜市口-上海浦东")
    
    -- 归属信息
    project_phase TEXT,           -- 建设期 (如 "8.1期", "10期")
    source_file TEXT,             -- 来源文件 (追溯用)
    source_sheet TEXT,            -- 来源sheet (追溯用)
    
    -- 系统属性
    system_type TEXT,             -- 系统性质 (如 "IP", "SDH", "CMNET")
    system_category TEXT,         -- 业务分类 (如 "长途", "光通道", "集客")
    capacity TEXT,                -- 容量 (如 "1*10Gb/s", "10G POS 1+1")
    protection_type TEXT,         -- 保护类型 (如 "1+1", "1+0")
    service_type TEXT,            -- 业务种类 (如 "10", "100", "100GE")
    business_nature TEXT,         -- 业务性质 (如 "集客", "国际", "业务网")
    
    -- 路由关系
    route_nature TEXT,            -- 路由性质 (主用/备用)
    protection_circuit TEXT,      -- 保护电路编号
    protection_endpoint TEXT,     -- 保护电路终端点
    
    -- 元信息
    update_date TEXT,             -- 数据更新时间
    remark TEXT,                  -- 备注
    raw_json TEXT                 -- 原始行数据JSON(保留未映射字段)
);

CREATE INDEX IF NOT EXISTS idx_circuits_system_name ON circuits(system_name);
CREATE INDEX IF NOT EXISTS idx_circuits_circuit_name ON circuits(circuit_name);
CREATE INDEX IF NOT EXISTS idx_circuits_circuit_no ON circuits(circuit_no);
CREATE INDEX IF NOT EXISTS idx_circuits_project_phase ON circuits(project_phase);

-- 全文搜索虚拟表
CREATE VIRTUAL TABLE IF NOT EXISTS circuits_fts USING fts5(
    circuit_no, system_name, circuit_name, endpoint,
    content='circuits', content_rowid='id',
    tokenize='unicode61'
);

-- 触发器: 同步circuits插入到FTS
CREATE TRIGGER IF NOT EXISTS circuits_ai AFTER INSERT ON circuits BEGIN
    INSERT INTO circuits_fts(rowid, circuit_no, system_name, circuit_name, endpoint)
    VALUES (new.id, new.circuit_no, new.system_name, new.circuit_name, new.endpoint);
END;

-- 触发器: 同步circuits删除
CREATE TRIGGER IF NOT EXISTS circuits_ad AFTER DELETE ON circuits BEGIN
    INSERT INTO circuits_fts(circuits_fts, rowid, circuit_no, system_name, circuit_name, endpoint)
    VALUES ('delete', old.id, old.circuit_no, old.system_name, old.circuit_name, old.endpoint);
END;

-- 触发器: 同步circuits更新
CREATE TRIGGER IF NOT EXISTS circuits_au AFTER UPDATE ON circuits BEGIN
    INSERT INTO circuits_fts(circuits_fts, rowid, circuit_no, system_name, circuit_name, endpoint)
    VALUES ('delete', old.id, old.circuit_no, old.system_name, old.circuit_name, old.endpoint);
    INSERT INTO circuits_fts(rowid, circuit_no, system_name, circuit_name, endpoint)
    VALUES (new.id, new.circuit_no, new.system_name, new.circuit_name, new.endpoint);
END;

-- 路由跳段详情表
CREATE TABLE IF NOT EXISTS circuit_hops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    circuit_no TEXT,              -- 关联电路编号
    system_name TEXT,             -- 关联系统名称
    
    hop_order INTEGER,           -- 跳次序号
    route_type TEXT,              -- 主用/备用
    
    -- 路由段信息
    station_a TEXT,               -- A端局站
    station_b TEXT,               -- B端局站
    timeslot_id TEXT,             -- 时隙ID (如 "M7578λ31-1")
    multiplex_section TEXT,       -- 复用段名称
    device_type TEXT,             -- 设备类型 (如 "OSN9800")
    
    -- A端设备详情 (14.2期+/17期+)
    a_equipment_id TEXT,          -- A网元ID
    a_line_slot TEXT,             -- A线路槽位
    a_line_port TEXT,             -- A线路端口
    a_line_board TEXT,            -- A线路板类型
    a_tributary_slot TEXT,        -- A支路槽位
    a_tributary_port TEXT,        -- A支路端口
    a_tributary_board TEXT,       -- A支路板类型
    
    -- B端设备详情
    b_equipment_id TEXT,
    b_line_slot TEXT,
    b_line_port TEXT,
    b_line_board TEXT,
    b_tributary_slot TEXT,
    b_tributary_port TEXT,
    b_tributary_board TEXT,
    
    -- 元信息
    source_file TEXT,
    source_sheet TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_hops_circuit_no ON circuit_hops(circuit_no);
CREATE INDEX IF NOT EXISTS idx_hops_system_name ON circuit_hops(system_name);

-- 复用段链路表 (15/16/17期主要数据)
CREATE TABLE IF NOT EXISTS multiplex_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 查询关联
    project_phase TEXT,           -- 建设期
    system_name TEXT,             -- 关联系统名
    
    -- 复用段核心
    link_id TEXT,                 -- 链路ID
    province TEXT,                -- 省份
    station TEXT,                 -- 局站
    device_type TEXT,             -- 设备类型
    platform TEXT,                -- 平台
    timeslot_id TEXT,             -- 时隙ID
    multiplex_section_name TEXT,  -- 复用段名称
    config_phase TEXT,            -- 配置期
    use_phase TEXT,               -- 使用期
    usage_type TEXT,              -- 本期使用 (新建/利旧)
    usage_nature TEXT,            -- 使用性质 (工作/保护)
    terminal_type TEXT,           -- 终端/转接
    rate TEXT,                    -- 速率
    
    source_file TEXT,
    source_sheet TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_mux_phase ON multiplex_sections(project_phase);
CREATE INDEX IF NOT EXISTS idx_mux_system ON multiplex_sections(system_name);
CREATE INDEX IF NOT EXISTS idx_mux_station ON multiplex_sections(station);

-- 预处理元信息表
CREATE TABLE IF NOT EXISTS preprocess_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

PRAGMA journal_mode=WAL;
PRAGMA synchronous=OFF;
"""


def create_schema(db_path: str):
    """创建数据库表结构"""
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
