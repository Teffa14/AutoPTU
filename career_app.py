"""Standalone Vercel entry point for AutoPTU Career.

The browser Career deployment only needs the Career API and its built SPA. Keeping
this entry point separate avoids importing the desktop/campaign battle server and
its large asset graph on every serverless cold start.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from auto_ptu.api.career_api import router as career_router


app = FastAPI(title="AutoPTU Career API")
app.include_router(career_router)

CAREER_STATIC_DIR = Path(__file__).resolve().parent / "public" / "career-game"
app.mount(
    "/career-game/assets",
    StaticFiles(directory=CAREER_STATIC_DIR / "assets", check_dir=False),
    name="career-assets",
)


@app.get("/api/v1/build", include_in_schema=False)
def deployed_build() -> dict[str, str]:
    return {
        "source_commit": str(
            os.environ.get("AUTOPTU_SOURCE_COMMIT")
            or os.environ.get("VERCEL_GIT_COMMIT_SHA")
            or "unknown"
        ).strip()
    }


@app.get("/career-game")
@app.get("/career-game/")
@app.get("/career-game/{path:path}")
def career_game(path: str = "") -> Response:
    entrypoint = CAREER_STATIC_DIR / "index.html"
    if not entrypoint.exists():
        resume_path = f"/career-game/{path.lstrip('/')}"
        return RedirectResponse(
            f"/career-game/index.html?resume={quote(resume_path, safe='')}",
            status_code=307,
        )
    return FileResponse(entrypoint, headers={"Cache-Control": "no-store"})


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse(
        "/career-game/",
        status_code=307,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


__all__ = ["app"]
