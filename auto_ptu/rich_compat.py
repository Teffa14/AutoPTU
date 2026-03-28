"""Compatibility helpers for Rich in bundled builds."""

from __future__ import annotations

import importlib
import os
import sys


def ensure_rich_unicode(preferred: str = "16.0.0") -> None:
    """Ensure Rich can resolve a unicode data module in bundled builds."""
    os.environ.setdefault("UNICODE_VERSION", preferred)
    # If Rich tries to import a unicode module that isn't bundled, alias it to a
    # known-good version to avoid crashing the UI.
    try:
        importlib.import_module("rich._unicode_data.unicode17-0-0")
        return
    except ModuleNotFoundError:
        pass
    try:
        fallback = importlib.import_module("rich._unicode_data.unicode16-0-0")
    except ModuleNotFoundError:
        return
    sys.modules.setdefault("rich._unicode_data.unicode17-0-0", fallback)
