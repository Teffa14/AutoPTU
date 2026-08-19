"""API surfaces for the Auto PTU engine."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine_facade import EngineFacade

__all__ = ["EngineFacade"]


def __getattr__(name: str):
    if name == "EngineFacade":
        from .engine_facade import EngineFacade

        return EngineFacade
    raise AttributeError(name)
