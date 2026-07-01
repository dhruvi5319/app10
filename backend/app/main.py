import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, log_startup_config
from app.database import init_db
from app.models.errors import ErrorResponse
from app.routers import chat, documents, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
    logger = logging.getLogger("app")
    logger.info("Starting RAG Chatbot backend...")

    await init_db(settings.DATABASE_URL)
    logger.info("Database initialized")

    log_startup_config(settings)

    yield

    logger.info("Shutting down RAG Chatbot backend")


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG Chatbot API",
        description="Backend API for document-grounded RAG chatbot",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
            ).model_dump(),
        )

    @app.get("/", tags=["health"])
    async def health_check():
        return {"status": "ok"}

    app.include_router(sessions.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")

    return app


app = create_app()
