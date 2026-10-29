from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, projects
from app.config import get_settings
from app.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(auth.router)
app.include_router(projects.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}