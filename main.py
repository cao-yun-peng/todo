from fastapi import FastAPI

from app.routers import (
    users,
    todos,
)


app = FastAPI(
    title="Todo API"
)


app.include_router(
    users.router
)

app.include_router(
    todos.router
)


@app.get("/")
def root():
    return {
        "message": "Todo backend is running"
    }