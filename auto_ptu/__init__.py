"""Auto PTU public package API."""
import os

# Ensure Rich uses an available unicode table inside bundled builds.
os.environ.setdefault("UNICODE_VERSION", "16.0.0")
from .data_loader import default_campaign, load_campaign, load_builtin_campaign, plan_from_campaign
from .engine import MatchEngine
from .matchmaker import AutoMatchPlanner
from .optimizer import BuildGenome, EncounterModel, default_encounter_model, score_build_genome

__all__ = [
    "default_campaign",
    "load_campaign",
    "load_builtin_campaign",
    "plan_from_campaign",
    "MatchEngine",
    "AutoMatchPlanner",
    "BuildGenome",
    "EncounterModel",
    "default_encounter_model",
    "score_build_genome",
]
