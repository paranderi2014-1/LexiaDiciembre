"""Punto de entrada de la API central LexIAParaguay (Plan Maestro §6)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.routes import admin, auth, catalog, chat, health
from app.services.cache import cache


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await cache.aclose()


app = FastAPI(
    title=settings.api_title,
    version="1.0.0",
    description=(
        "API central compartida por la web y Android. Verifica ID tokens de Firebase, "
        "aplica roles y permisos de PostgreSQL y responde con fundamento documental citado."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (health, auth, chat, catalog, admin):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")
