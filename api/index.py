"""Vercel ASGI entry point for the authoritative AutoPTU application."""

from auto_ptu.api.server import app as auto_ptu_app

app = auto_ptu_app

__all__ = ["app"]
