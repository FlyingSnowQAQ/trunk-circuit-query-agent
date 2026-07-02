"""
智能体编排引擎

核心编排函数 run_agent() 实现了三步推理流程：
1. LLM 意图识别 → 提取系统名/电路编号
2. 查所属工程期数（lookup_phase）
3. 查路由详情（query_routing）

输出结构化的 steps[] 数组，前端可直接渲染。
"""
import re
from typing import Optional
from agent.tools import lookup_phase, query_routing
from agent.llm_client import LLMClient


def _is_abbr_code_name(name: str) -> bool:
    """判断电路名是否为站名+代号+数字类（如 北京CR1-上海CR1, 北京JS1-上海JS1, 北京T2-武汉T1）"""
    return bool(re.search(r'[A-Z]{1,4}\d', name))


def _clean_query(text: str) -> str:
    """降级模式下清理用户输入，提取核心系统名"""
    # 去除常见前缀
    text = re.sub(r'^(查一下|查查|查找|查询|找一下|找找|搜索|看看|帮我查|帮我找)\s*', '', text)
    # 去除常见后缀（路由/详情/信息/的/等）
    text = re.sub(r'\s*(的路由|路由|详情|的信息|信息|的数据|的数据路由)\s*$', '', text)
    text = re.sub(r'的$', '', text)
    return text.strip()


def run_agent(user_query: str, llm: Optional[LLMClient] = None) -> dict:
    """
    智能体主编排函数

    参数:
        user_query: 用户的自然语言查询（如 "查一下北京-上海39系统的路由"）
        llm:        LLM客户端（可选，不传则走纯SQL降级模式）

    返回:
        {
            "query": str,            # 原始查询
            "steps": list[dict],     # 三步推理结果
            "llm_summary": str,      # AI总结（可选）
        }
    """
    steps = []
    llm_summary = ""

    # ============ 步骤0: 意图识别 ============
    cleaned = _clean_query(user_query)
    intent = {"system_name": cleaned, "circuit_no": "", "intent": "search_system"}
    if llm and llm.available:
        intent = llm.analyze_intent(user_query)

    system_name = intent.get("system_name", "") or user_query
    circuit_no = intent.get("circuit_no", "")
    query_intent = intent.get("intent", "search_system")

    steps.append({
        "step": 1,
        "title": "识别传输系统名",
        "status": "completed",
        "detail": {
            "raw_input": user_query,
            "extracted_system": system_name,
            "extracted_circuit_no": circuit_no,
            "intent": query_intent,
            "confidence": intent.get("confidence", 0),
        },
        "description": (
            f"从输入中识别出传输系统名"
            f"【{system_name or circuit_no}】"
            if system_name or circuit_no
            else "未能识别出具体的传输系统名"
        ),
    })

    # ============ 步骤1: 查所属工程期数 ============
    phase_result = {"found": False, "phase": None, "circuits": [], "match_type": "未匹配"}

    if circuit_no:
        # 按电路编号查找
        from agent.tools import search_circuits
        sr = search_circuits(circuit_no, page_size=10)
        if sr["results"]:
            phase_result["found"] = True
            phase_result["phase"] = sr["results"][0].get("project_phase", "")
            phase_result["circuits"] = sr["results"]
            phase_result["match_type"] = "电路编号匹配"

    if not phase_result["found"] and system_name:
        phase_result = lookup_phase(system_name)

    # 降级搜索：用原始输入尝试在所有字段中搜索（电路号 / 系统名 / 电路名）
    if not phase_result["found"]:
        from agent.tools import search_circuits
        sr = search_circuits(user_query, page_size=10)
        if sr["results"]:
            phase_result["found"] = True
            phase_result["phase"] = sr["results"][0].get("project_phase", "")
            phase_result["circuits"] = sr["results"]
            phase_result["match_type"] = "全字段匹配"

    # LLM辅助模糊匹配（如果未找到且有LLM）
    if not phase_result["found"] and llm and llm.available:
        corrected_name = llm.fuzzy_correct(system_name)
        if corrected_name and corrected_name != system_name:
            phase_result = lookup_phase(corrected_name)
            if phase_result["found"]:
                phase_result["match_type"] = f"LLM纠错匹配（{corrected_name}）"
                system_name = corrected_name  # 更新系统名

    steps.append({
        "step": 2,
        "title": "查询所属工程期数",
        "status": "completed" if phase_result["found"] else "not_found",
        "detail": phase_result,
        "description": (
            f"查得【{system_name}】属于【{phase_result['phase']}】工程"
            if phase_result["found"]
            else f"未在电路汇总表中找到【{system_name}】"
        ),
    })

    # ============ 步骤2: 查路由详情 ============
    routing_result = {"has_hops": False, "total_hops": 0, "has_device_detail": False, "hops": []}

    if phase_result["found"]:
        matched_circuits = phase_result.get("circuits", [])
        target_phase = phase_result.get("phase", "")

        # 从匹配到的电路中收集查询参数
        # circuit_name 跨期也收集（可能其他期有更完整路由数据）
        all_circuit_nos = []
        all_system_names = []
        all_circuit_names = []
        all_raw_circuit_names = []  # 未过滤的原始电路名，用于兜底查询
        for circuit in matched_circuits:
            cname = circuit.get("circuit_name", "")
            # 跳过站名+代号+数字类电路名（如 北京CR1-上海CR1, 北京JS1-上海JS1, 北京T2-武汉T1）
            if cname and not _is_abbr_code_name(cname):
                all_circuit_names.append(cname)
            # 原始电路名全部保留（含被过滤的），仅用于兜底查询数据
            if cname:
                all_raw_circuit_names.append(cname)
            # circuit_no / system_name 限本期，避免跨期混淆
            if circuit.get("project_phase", "") != target_phase:
                continue
            if circuit.get("circuit_no"):
                all_circuit_nos.append(circuit["circuit_no"])
            if circuit.get("system_name"):
                all_system_names.append(circuit["system_name"])

        # 四级匹配：circuit_name+phase → circuit_name → circuit_no → system_name
        # —— 优先选站名完整的结果，而非第一个碰到的 ——

        def _count_filled_stations(hops: list) -> int:
            """统计跳段中站名非空的数量"""
            return sum(1 for h in hops if h.get("station_a") or h.get("station_b"))

        def _pick_best(candidates: list) -> dict:
            """从候选结果中选站名最完整的；若都为空站则视为无有效匹配"""
            if not candidates:
                return {"has_hops": False, "total_hops": 0, "hops": []}
            candidates.sort(key=lambda x: _count_filled_stations(x.get("hops", [])), reverse=True)
            best = candidates[0]
            # 如果最佳候选的站名全部为空，视为无效匹配
            if _count_filled_stations(best.get("hops", [])) == 0:
                return {"has_hops": False, "total_hops": 0, "hops": []}
            return best

        # 优先级1: circuit_name + project_phase 双重匹配（最精准）
        if not routing_result["has_hops"] and all_circuit_names:
            phase_candidates = []
            for cname in set(all_circuit_names):
                if not cname:
                    continue
                detail = query_routing(circuit_name=cname, project_phase=target_phase)
                if detail["has_hops"]:
                    detail["circuit_name"] = cname
                    detail["project_phase"] = target_phase
                    detail["match_context"] = f"系统「{system_name}」→ {cname} @ {target_phase}"
                    phase_candidates.append(detail)
            if phase_candidates:
                routing_result = _pick_best(phase_candidates)

        # 优先级2: circuit_name 仅匹配（可能跨期，补充原文系统名）
        if not routing_result["has_hops"] and all_circuit_names:
            name_candidates = []
            for cname in set(all_circuit_names):
                if not cname:
                    continue
                detail = query_routing(circuit_name=cname)
                if detail["has_hops"]:
                    detail["circuit_name"] = cname
                    detail["match_context"] = f"电路名称匹配: {cname}（源自系统「{system_name}」）"
                    name_candidates.append(detail)
            if name_candidates:
                routing_result = _pick_best(name_candidates)

        # 优先级3: 原始输入作为电路名兜底（解决 abbr-code 过滤后无候选的问题）
        if not routing_result["has_hops"] and system_name:
            detail = query_routing(circuit_name=system_name, project_phase=target_phase)
            if not detail["has_hops"]:
                detail = query_routing(circuit_name=system_name)
            if detail["has_hops"]:
                if _count_filled_stations(detail.get("hops", [])) > 0:
                    routing_result = detail
                    routing_result["match_context"] = f"原始输入匹配: {system_name}"

        # 优先级4: circuit_no 匹配
        if not routing_result["has_hops"]:
            for cn in all_circuit_nos:
                detail = query_routing(circuit_no=cn)
                if detail["has_hops"]:
                    routing_result = detail
                    routing_result["circuit_no"] = cn
                    routing_result["match_context"] = f"电路编号匹配: {cn}"
                    break

        # 优先级4: system_name LIKE 模糊匹配
        if not routing_result["has_hops"] and all_system_names:
            for sn in all_system_names:
                detail = query_routing(system_name=sn)
                if detail["has_hops"]:
                    routing_result = detail
                    routing_result["match_context"] = f"系统名模糊匹配: {sn}"
                    break

        # 优先级5: 用原始电路名（含被过滤的abbr-code）兜底查询，但显示系统名
        if not routing_result["has_hops"] and all_raw_circuit_names:
            raw_candidates = []
            for cname in set(all_raw_circuit_names):
                if not cname:
                    continue
                detail = query_routing(circuit_name=cname)
                if detail["has_hops"]:
                    detail["circuit_name"] = cname
                    detail["match_context"] = f"系统「{system_name}」"
                    raw_candidates.append(detail)
            if raw_candidates:
                routing_result = _pick_best(raw_candidates)

    steps.append({
        "step": 3,
        "title": "查询路由详情",
        "status": "completed" if routing_result["has_hops"] else "no_data",
        "detail": routing_result,
        "description": (
            f"在路由表中查得 {routing_result['total_hops']} 条路由跳段"
            + (f" · {routing_result.get('match_context', '')}" if routing_result.get("match_context") else "")
            if routing_result["has_hops"]
            else "该电路无详细路由数据"
        ),
    })

    # ============ LLM 格式化总结 ============
    if llm and llm.available:
        try:
            llm_summary = llm.format_summary(user_query, steps)
        except Exception:
            llm_summary = ""

    return {
        "query": user_query,
        "steps": steps,
        "llm_summary": llm_summary,
    }
