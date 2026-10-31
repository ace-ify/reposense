from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env variables into os.environ
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.evaluation import router as evaluation_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.questions import router as questions_router
from backend.app.api.routes.samples import router as samples_router
from backend.app.core.config import get_settings
from backend.app.pipeline.registry import get_registry
from backend.app.pipeline.sample_data import seed_sample_documents

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Synthetic sample PDFs are only created when explicitly enabled for local demos.
    if settings.seed_sample_documents:
        seed_sample_documents(get_registry())
    yield

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes under /api/v1 (Official API Contract)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(documents_router, prefix=settings.api_prefix)
app.include_router(questions_router, prefix=settings.api_prefix)
app.include_router(samples_router, prefix=settings.api_prefix)
app.include_router(evaluation_router, prefix=settings.api_prefix)

# Root level health probe (standard for container/orchestrator health checks)
app.include_router(health_router)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.api_prefix,
    }
