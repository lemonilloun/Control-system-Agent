import logging
from fastapi import FastAPI

from app.routers import agent, health

# Basic logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    application = FastAPI(title="Control System Agent", version="0.1.0")
    application.include_router(health.router, prefix="/health", tags=["health"])
    application.include_router(agent.router, prefix="/v1", tags=["agent"])
    return application


app = create_app()
