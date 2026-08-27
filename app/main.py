from fastapi import FastAPI

from app.routers.ticket_router import router as ticket_router
from app.routers.workflow_definition_router import router as workflow_definition_router
from app.routers.workflow_selector_router import router as workflow_selector_router

# 初始化 FastAPI 应用主入口，设置 Swagger 文档的标题与描述
app = FastAPI(
    title="AI Ticket Workflow Platform",
    description="A backend platform for client issue triage and workflow automation.",
    version="0.3.0",
)

# 挂载工单路由模块 (Ticket Router)
app.include_router(ticket_router)

# 挂载工作流定义路由模块 (Workflow Definition Router)
app.include_router(workflow_definition_router)

app.include_router(workflow_selector_router)

@app.get("/health")
def health_check():
    """系统健康检查接口"""
    return {
        "status": "ok"
    }

