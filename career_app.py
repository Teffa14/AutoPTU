"""Standalone AutoPTU Career API entry point.

GitHub Pages serves the Career SPA. This FastAPI app remains the independent
Career backend for catalog, run mutations, battles, and build provenance.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from auto_ptu.api.career_api import router as career_router


DEFAULT_CAREER_WEB_URL = "https://teffa14.github.io/AutoPTU/career-game"
DEFAULT_CORS_ORIGINS = (
    "https://teffa14.github.io",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
)


def _cors_origins() -> list[str]:
    configured = str(os.environ.get("CAREER_CORS_ORIGINS") or "").strip()
    if not configured:
        return list(DEFAULT_CORS_ORIGINS)
    return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]


app = FastAPI(title="AutoPTU Career API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(career_router)

CAREER_STATIC_DIR = Path(__file__).resolve().parent / "public" / "career-game"
app.mount(
    "/career-game/assets",
    StaticFiles(directory=CAREER_STATIC_DIR / "assets", check_dir=False),
    name="career-assets",
)


def _career_web_url(path: str = "") -> str:
    base = str(os.environ.get("CAREER_WEB_URL") or DEFAULT_CAREER_WEB_URL).strip().rstrip("/")
    suffix = quote(path.lstrip("/"), safe="/")
    return f"{base}/{suffix}" if suffix else f"{base}/"


@app.get("/api/v1/build", include_in_schema=False)
def deployed_build() -> dict[str, str]:
    return {
        "source_commit": str(os.environ.get("AUTOPTU_SOURCE_COMMIT") or "unknown").strip()
    }


@app.get("/career-game")
@app.get("/career-game/")
@app.get("/career-game/{path:path}")
def career_game(path: str = "") -> Response:
    entrypoint = CAREER_STATIC_DIR / "index.html"
    if not entrypoint.exists():
        return RedirectResponse(
            _career_web_url(path),
            status_code=307,
            headers={"Cache-Control": "no-store"},
        )
    return FileResponse(entrypoint, headers={"Cache-Control": "no-store"})


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse(
        _career_web_url(),
        status_code=307,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


__all__ = ["app"]
