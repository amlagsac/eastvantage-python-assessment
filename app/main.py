from app.api.v1.exceptions import AppError
import logging
import asyncio
from contextlib import asynccontextmanager

from app.core.config import Settings, get_settings

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.logging import configure_logging
from app.db.session import Base, engine


settings: Settings = get_settings()

logger = logging.getLogger(__name__)
configure_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(Base.metadata.create_all, bind=engine)
        logger.info("Application started")
        yield
    except Exception:
        logger.exception("Application lifespan failed")
        raise
    finally:
        logger.info("Application shutting down")
        engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Address Book API by Andre Lagsac for Eastvantage Technical Exam.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(AppError)
def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    logger.warning("%s: %s", type(exc).__name__, exc)
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})
