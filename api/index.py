"""Vercel ASGI entry point for the authoritative AutoPTU application."""

from auto_ptu.api.server import app

__all__ = ["app"]
