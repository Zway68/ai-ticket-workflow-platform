from fastapi import FastAPI
from app.routers import ticket_router

app = FastAPI(title="AI Ticket Workflow Platform API")

app.include_router(ticket_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to AI Ticket Workflow Platform API"}
