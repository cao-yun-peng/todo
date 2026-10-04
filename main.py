from fastapi import FastAPI

from app.database import (
    Base,
    engine,
)

from app import models

from app.routers import (
    users,
    todos,
)


Base.metadata.create_all(
    bind=engine
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