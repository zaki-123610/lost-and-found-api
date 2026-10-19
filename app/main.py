from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the database tables once, before the server accepts requests."""
    init_db()
    yield


app = FastAPI(
    title="Lost & Found API",
    description="Report lost and found items, search them, and mark them as recovered.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness check. Does not touch the database."""
    return {"status": "ok"}
