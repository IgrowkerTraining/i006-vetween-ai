"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request,status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1 import api_router
from app.models.schemas import RootResponse
from app.services.ai_service import ai_service

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    await ai_service.close()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI template with NVIDIA NMI AI integration",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 1. Extraemos los errores de Pydantic
    errors = exc.errors()
    
    for error in errors:
        # Aquí capturamos tu mensaje: "Inconsistencia: Felinos con vacuna Séxtuple canina"
        msg = error.get("msg")
        loc = error.get("loc")
        
        # 2. LO FORZAMOS AL LOG AQUÍ (Esto no puede fallar)
        logger.error(f"ERROR DE NEGOCIO DETECTADO: {msg} en {loc}")

    # 3. Retornamos el 422 original para no romper el contrato con el frontend
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "Los datos enviados son inconsistentes o invalidos",
            "details": errors  # Aquí viaja tu "Inconsistencia detectada: El paciente es Felinos..."
        }
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API routers
app.include_router(api_router)


@app.get("/", response_model=RootResponse)
async def read_root():
    """Root endpoint with basic information."""
    return RootResponse(
        message=f"Welcome to {settings.app_name}",
        version=settings.app_version,
        docs="/docs",
        health="/api/v1/health"
    )


# Legacy endpoint for backward compatibility
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Example endpoint from original template."""
    return {"item_id": item_id, "q": q}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
