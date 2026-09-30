"""API Idéomès : `uvicorn app.main:app --reload` depuis le dossier api/."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .base import initialiser
from .config import reglages
from .routers import assets, db, dossiers, moi

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s : %(message)s")


@asynccontextmanager
async def cycle_de_vie(_app):
    initialiser()
    yield


app = FastAPI(
    title="Idéomès API",
    version="0.1.0",
    lifespan=cycle_de_vie,
    description="Base de l'application Idéomès (Geomessen) et pilotage des agents IA.",
)
app.add_middleware(
    CORSMiddleware, allow_origins=reglages.cors_origines.split(","), allow_methods=["*"], allow_headers=["*"]
)
for routeur in (db.r, moi.r, assets.r, dossiers.r):
    app.include_router(routeur)


@app.get("/api/sante")
def sante():
    from ideomes_agents.config import reglages as ra

    return {"ok": True, "llm_mode": ra.llm_mode, "pipeline_auto": reglages.pipeline_auto}


@app.get("/", include_in_schema=False)
def accueil():
    index = reglages.web_dist / "index.html"
    if not index.exists():
        return JSONResponse({"message": "Construisez l'appli : python web/build.py"}, status_code=503)
    return FileResponse(index)
