"""
Pydantic 请求/响应模型

定义 API 的请求体、响应体等数据结构。
"""
from pydantic import BaseModel, Field
from typing import Optional


class AgentQueryRequest(BaseModel):
    """智能体查询请求"""
    query: str = Field(..., description="用户的自然语言查询", min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, description="会话ID（可选）")


class StepDetail(BaseModel):
    """单步推理结果"""
    step: int
    title: str
    status: str  # completed / not_found / no_data
    description: str
    detail: dict


class AgentQueryResponse(BaseModel):
    """智能体查询响应"""
    code: int = 0
    message: str = "ok"
    data: dict


class HealthResponse(BaseModel):
    """健康检查响应"""
    code: int = 0
    message: str = "ok"
    data: dict


class SearchRequest(BaseModel):
    """快捷搜索请求（query参数）"""
    q: str = Field(..., description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class DetailRequest(BaseModel):
    """快捷详情请求（query参数）"""
    circuit_no: Optional[str] = Field(None, description="电路编号")
    system_name: Optional[str] = Field(None, description="系统名称")
