"""
Empire & Ink — Main Entrypoint

FastAPI + Jinja2 Templates. One service, one Render web service.

Start locally:   python main.py
Start (prod):    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.api.routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("empire_ink")

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("═" * 55)
    logger.info("  Empire & Ink — AI Mughal Art Studio")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  Supabase    : {settings.supabase_url[:40]}…")
    logger.info("═" * 55)
    yield
    logger.info("Empire & Ink shutting down.")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Empire & Ink API",
    description="AI-powered Mughal miniature art generator",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# API routes
app.include_router(api_router)


# ── Page routes ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/studio", response_class=HTMLResponse)
async def studio_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/gallery", response_class=HTMLResponse)
async def gallery_page(request: Request):
    return templates.TemplateResponse("gallery.html", {"request": request})


# ── Local development runner ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=not settings.is_production,
        log_level="info",
    )
