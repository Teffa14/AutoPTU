"""Server-authoritative career mode built on the AutoPTU rules engine."""

from .engine import CareerEngine
from .leaderboard_names import install_leaderboard_name_fix
from .models import CareerRun

install_leaderboard_name_fix()

# The public API imports CareerService from this module after package import.
# Replace that exported class with the presentation-aware subclass without
# changing battle mechanics or the API route surface.
from . import service as _service
from .advanced_service import AdvancedCareerService

_service.CareerService = AdvancedCareerService

__all__ = ["CareerEngine", "CareerRun", "AdvancedCareerService"]
