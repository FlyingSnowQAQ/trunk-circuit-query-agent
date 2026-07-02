"""
FastAPI 应用和服务

提供 REST API 端点：
- GET  /api/health           — 健康检查
- POST /api/agent/query      — 智能体查询（主入口）
- GET  /api/circuits/search  — 快捷搜索
- GET  /api/circuits/detail  — 快捷详情

同时渲染 Web UI 页面。
"""
import os
import sys

# 确保项目根目录在 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config import DB_PATH, ENABLE_LLM
from agent.engine import run_agent
from agent.llm_client import LLMClient
from agent.tools import search_circuits, query_routing, get_db_stats
from api.schemas import AgentQueryRequest


# ---------- LLM 客户端 ----------
llm_client = LLMClient() if ENABLE_LLM else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时检查
    db_exists = os.path.exists(DB_PATH)
    if not db_exists:
        print(f"[!] 数据库未找到: {DB_PATH}")
        print("[!] 请先运行 circuit-query-system 的 preprocess.py 构建数据库")
    else:
        size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        print(f"[✓] 数据库加载成功: {size_mb:.0f} MB")
        print(f"[✓] LLM 状态: {'已启用' if llm_client and llm_client.available else '未配置（降级模式）'}")

    yield


app = FastAPI(
    title="移动干线电路查询智能体 API",
    description="中国移动一干传输电路路由查询 — 智能体三步推理引擎",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------- 静态文件和模板 ----------
static_dir = os.path.join(ROOT, "web", "static")
templates_dir = os.path.join(ROOT, "web", "templates")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 使用 Jinja2 直接渲染，避免 Starlette Jinja2Templates 兼容问题
from jinja2 import Environment, FileSystemLoader
jinja_env = Environment(loader=FileSystemLoader(templates_dir), auto_reload=False)


# ========== API 端点 ==========

@app.get("/api/health")
async def health():
    """健康检查"""
    try:
        stats = get_db_stats()
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "status": "healthy",
                "db_path": DB_PATH,
                "db_exists": os.path.exists(DB_PATH),
                "llm_enabled": llm_client.available if llm_client else False,
                **stats,
            },
        }
    except Exception as e:
        return {"code": -1, "message": str(e), "data": {}}


@app.post("/api/agent/query")
async def agent_query(req: AgentQueryRequest):
    """
    智能体查询（主入口）

    三步推理：
    1. 识别传输系统名
    2. 查所属工程期数
    3. 查路由详情
    """
    try:
        result = run_agent(req.query, llm=llm_client)
        return {"code": 0, "message": "ok", "data": result}
    except Exception as e:
        return {"code": -1, "message": f"查询异常: {str(e)}", "data": {}}


@app.get("/api/circuits/search")
async def circuits_search(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """快捷搜索电路（跳过智能体）"""
    try:
        result = search_circuits(q, page, page_size)
        return {"code": 0, "message": "ok", "data": result}
    except Exception as e:
        return {"code": -1, "message": str(e), "data": {}}


@app.get("/api/circuits/detail")
async def circuits_detail(
    circuit_no: str = Query("", description="电路编号"),
    system_name: str = Query("", description="系统名称"),
    circuit_name: str = Query("", description="电路名称"),
    project_phase: str = Query("", description="工程期数"),
):
    """快捷查询路由详情"""
    try:
        result = query_routing(
            circuit_no=circuit_no or None,
            system_name=system_name or None,
            circuit_name=circuit_name or None,
            project_phase=project_phase or None,
        )
        return {"code": 0, "message": "ok", "data": result}
    except Exception as e:
        return {"code": -1, "message": str(e), "data": {}}


# ========== Web UI ==========

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Web UI 主页面"""
    template = jinja_env.get_template("index.html")
    html = template.render(
        title="移动干线电路查询智能体",
        llm_enabled=llm_client.available if llm_client else False,
    )
    return HTMLResponse(content=html)


# ========== 启动入口 ==========
if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT

    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")
