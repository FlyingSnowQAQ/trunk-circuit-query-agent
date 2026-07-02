"""
列映射规则配置

汇总Excel的15个sheet具有不同的列结构和列名，
此模块定义每个sheet到统一字段的映射规则。
"""
import json

# ========= 汇总Excel各Sheet的列映射规则 =========
# 格式: {
#   "sheet名称": {
#       "phase": "建设期名称",
#       "header_rows": 表头行数(0=第一行即表头),
#       "extra_skip_rows": 额外跳过的非数据行(如第1行总标题),
#       "skip_empty_circuit": 是否跳过电路号为空的行,
#       "columns": { "源列名": "目标字段名" }
#   }
# }

SHEET_MAP = {
    "567期": {
        "phase": "567期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路编号": "circuit_no",
            "系统名称": "system_name",
            "电路名称": "circuit_name",
            "终端点": "endpoint",
            "系统性质": "system_type",
            "容量": "capacity",
            "建设期": "project_phase",
        }
    },
    "8.1期": {
        "phase": "8.1期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路编号": "circuit_no",
            "系统名称": "system_name",
            "电路名称": "circuit_name",
            "终端点": "endpoint",
            "系统性质": "system_type",
            "容量": "capacity",
            "建设期": "project_phase",
        }
    },
    "8.2期": {
        "phase": "8.2期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路编号": "circuit_no",
            "系统名称": "system_name",
            "电路名称": "circuit_name",
            "终端点": "endpoint",
            "系统性质": "system_type",
            "容量": "capacity",
            "建设期": "project_phase",
        }
    },
    "9.1期": {
        "phase": "9.1期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路名称": "circuit_name",
            "电路编号": "circuit_no",
        }
    },
    "9.2期": {
        "phase": "9.2期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路编号": "circuit_no",
            "系统名称": "system_name",
            "电路名称": "circuit_name",
            "终端点": "endpoint",
            "系统性质": "system_type",
            "容量": "capacity",
            "建设期": "project_phase",
        }
    },
    "10期": {
        "phase": "10期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路号": "circuit_no",
            "系统名称": "system_name",
            "电路名称": "circuit_name",
            "终端点": "endpoint",
            "业务性质": "business_nature",
            "系统性质": "system_type",
            "容量": "capacity",
            "传输建设期": "project_phase",
            "数据更新时间": "update_date",
        }
    },
    "11.1期": {
        "phase": "11.1期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路号": "circuit_no",
            "系统名称": "system_name",
            "电路名称": "circuit_name",
            "终端点": "endpoint",
            "业务性质": "business_nature",
            "业务种类": "service_type",
            "保护类型": "protection_type",
            "接口种类": "capacity",
            "传输建设期": "project_phase",
            "数据更新时间": "update_date",
        }
    },
    "11.2期": {
        "phase": "11.2期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路编号": "circuit_no",
            "系统": "system_name",
            "电路名称": "circuit_name",
            "终端点": "endpoint",
        }
    },
    "12期": {
        "phase": "12期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路编号": "circuit_no",
            "系统名称": "system_name",
            "业务名称": "circuit_name",
            "终端点": "endpoint",
            "业务性质": "business_nature",
            "业务种类": "service_type",
            "保护类型": "protection_type",
            "接口种类": "capacity",
            "传输建设期": "project_phase",
            "路由性质": "route_nature",
            "备注": "remark",
            "保护电路": "protection_circuit",
            "保护电路终端点": "protection_endpoint",
        }
    },
    "13期": {
        "phase": "13期",
        "header_rows": 2,  # 前2行是标题行，第3行是表头(0-index=2)
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路号": "circuit_no",
            "系统名称": "system_name",
            "终端点": "endpoint",
            "电路名称": "circuit_name",
            "系统性质": "system_type",
            "业务分类": "system_category",
            "保护类型": "protection_type",
            "业务种类": "service_type",
            "跳数": None,  # 忽略，直接解析路由数据
            "跳次": None,
            "路由": None,
            "路由A站": None,
            "路由B站": None,
            "时隙ID": None,
            "复用段名称": None,
            "设备类型": None,
            "备注": "remark",
        }
    },
    "14.1期": {
        "phase": "14.1期",
        "header_rows": 2,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路号": "circuit_no",
            "系统名称": "system_name",
            "终端点": "endpoint",
            "电路名称": "circuit_name",
            "系统性质": "system_type",
            "业务分类": "system_category",
            "保护类型": "protection_type",
            "业务种类": "service_type",
            "备注": "remark",
        }
    },
    "14.2期": {
        "phase": "14.2期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": True,
        "columns": {
            "电路号": "circuit_no",
            "系统名称": "system_name",
            "终端点": "endpoint",
            "电路名称": "circuit_name",
            "系统性质": "system_type",
            "业务分类": "system_category",
            "保护类型": "protection_type",
            "业务种类": "service_type",
        }
    },
    "15期": {
        "phase": "15期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": False,  # 15期无电路号
        "columns": {
            "系统": "system_name",
            "建设期": "project_phase",
            "省份": None,
            "局站": None,
            "设备类型": None,
            "平台": None,
            "时隙ID": None,
            "复用段名称": None,
        }
    },
    "16期": {
        "phase": "16期",
        "header_rows": 0,
        "extra_skip_rows": 0,
        "skip_empty_circuit": False,
        "columns": {
            "系统": "system_name",
            "建设期": "project_phase",
        }
    },
    "17期": {
        "phase": "17期",
        "header_rows": 1,  # 第1行是标题行"附表03：XX省市区十七期扩容工程波道配置表"
        "extra_skip_rows": 0,
        "skip_empty_circuit": False,
        "columns": {
            "系统": "system_name",
            "建设期": "project_phase",
        }
    },
}


# ========= 路由表文件到建设期的映射 =========
ROUTE_FILE_MAP = [
    # (文件路径关键词, 建设期, 文件类型, 表头行偏移, 编码)
    ("7期光通道路由表", "7期", "doc", 0, None),
    ("8.1期通道路由表", "8.1期", "xls", 0, None),
    ("8.2期波道配置表", "8.2期", "xls", 0, None),
    ("9.1期阶段波道配置表", "9.1期", "xls", None, "gbk"),
    ("9.2期波道配置表", "9.2期", "xlsx", 0, None),
    ("9.2期路由表", "9.2期", "xlsx", 0, None),
    ("10期光通道路由表", "10期", "xlsx", 0, None),
    ("11.1期光通道路由表", "11.1期", "xlsx", 0, None),
    ("11.2期波道配置表", "11.2期", "xlsx", 0, None),
    ("12期光通道路由表", "12期", "xlsx", 0, None),
    ("13.1期电路表", "13.1期", "xlsx", 0, None),
    ("13.3期电路表", "13.3期", "xlsx", 0, None),
    ("14.1期云专网", "14.1期", "xlsx", None, None),
    ("14.2期电路表汇总", "14.2期", "xlsx", 0, None),
    ("15.1期电路表", "15.1期", "xlsx", 0, None),
    ("16期扩容工程波道配置表", "16期", "xlsx", None, None),
    ("17期400G", "17期", "xlsx", None, None),
]


def build_phase_to_files_mapping(route_dir: str, files: list) -> dict:
    """
    根据文件名匹配构建 {建设期: [文件路径]} 映射
    """
    import os
    phase_map = {}
    for fname in files:
        fpath = os.path.join(route_dir, fname)
        matched = False
        for (keyword, phase, ftype, _, _) in ROUTE_FILE_MAP:
            if keyword in fname:
                phase_map.setdefault(phase, []).append({
                    "path": fpath,
                    "type": ftype,
                    "matched_by": keyword
                })
                matched = True
                break
        if not matched:
            # 未匹配的文件也记录
            phase_map.setdefault("_unmatched", []).append(fpath)
    return phase_map
