import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse

from backend.app.core.config import settings
from backend.app.core.observability import setup_observability
from backend.app.api.routes import router as api_router
from backend.app.api.websocket import ws_manager
from backend.app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize DB tables and background resources."""
    logger.info("Initializing AI Startup Co-Founder Team backend...")
    setup_observability()
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization skipped or deferred: {e}")
    yield
    logger.info("Shutting down backend services...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-agent co-founder system turning one-line ideas into market analysis, PRD, architecture, and pitch deck.",
    lifespan=lifespan
)

from backend.app.models.schemas import HealthResponse

# CORS configuration (ARCHITECTURE.md, SECURITY.md)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Root health check endpoint (API_SPEC.md)
@app.get("/health", response_model=HealthResponse)
async def root_health_check():
    """Healthcheck endpoint."""
    return HealthResponse(status="ok", version=settings.APP_VERSION)

# Include API Router
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format validation errors matching API_SPEC.md § Errors (HTTP 400)."""
    error_msg = "; ".join([f"{err.get('loc', [''])[ -1]}: {err.get('msg', '')}" for err in exc.errors()])
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "VALIDATION_ERROR", "message": error_msg}}
    )


# WebSocket Streaming Endpoint (API_SPEC.md § WebSocket)
@app.websocket("/ws/runs/{run_id}")
async def websocket_run_endpoint(websocket: WebSocket, run_id: str):
    """Real-time event streaming for an active run (API_SPEC.md § WebSocket)."""
    await ws_manager.connect(run_id, websocket)
    try:
        while True:
            # Keep socket alive and accept ping/pong or client commands
            data = await websocket.receive_text()
            logger.debug(f"Received client message on {run_id}: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(run_id, websocket)
    except Exception as e:
        logger.warning(f"WebSocket error for {run_id}: {e}")
        ws_manager.disconnect(run_id, websocket)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
