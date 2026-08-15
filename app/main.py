from fastapi import FastAPI

from app.routers.ticket_router import router as ticket_router

app = FastAPI(
    title="AI Ticket Workflow Platform",
    description="A backend platform for client issue triage and workflow automation.",
    version="0.1.0",
)

app.include_router(ticket_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
