from __future__ import annotations

import copy
import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from .models import CareerDecision


class NarrativeRenderer:
    """Optional Ollama prose layer; mechanics are immutable by construction."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        model_digest: Optional[str] = None,
        cache_root: Optional[Path] = None,
        timeout_seconds: float = 2.5,
    ) -> None:
        self.base_url = (base_url or os.environ.get("OLLAMA_URL") or "").rstrip("/")
        if self.base_url and "://" not in self.base_url:
            self.base_url = f"http://{self.base_url}"
        self.model = model or os.environ.get("OLLAMA_MODEL") or ""
        self.model_digest = model_digest or os.environ.get("OLLAMA_MODEL_DIGEST") or ""
        self.cache_root = cache_root or Path(os.environ.get("AUTO_PTU_RUNTIME_ROOT") or Path.cwd()) / "portable_data" / "career" / "narrative_cache"
        self.timeout_seconds = timeout_seconds

    def render(self, decision: CareerDecision, context: Dict[str, Any], locale: str) -> CareerDecision:
        fallback = copy.deepcopy(decision)
        if not self._configured():
            return fallback
        mechanical_before = _mechanical_signature(fallback)
        key = self._cache_key(fallback, context, locale)
        cached = self._read_cache(key)
        prose = cached or self._request_prose(fallback, context, locale)
        if not prose:
            return fallback
        rendered = _apply_prose(fallback, prose)
        if _mechanical_signature(rendered) != mechanical_before:
            return fallback
        if cached is None:
            self._write_cache(key, prose)
        return rendered

    def _configured(self) -> bool:
        return bool(
            self.base_url
            and self.model
            and self.model_digest.startswith("sha256:")
            and len(self.model_digest) == 71
        )

    def _cache_key(self, decision: CareerDecision, context: Dict[str, Any], locale: str) -> str:
        payload = {
            "decision": asdict(decision),
            "context": context,
            "locale": "es" if locale.lower().startswith("es") else "en",
            "model": self.model,
            "model_digest": self.model_digest,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def _request_prose(self, decision: CareerDecision, context: Dict[str, Any], locale: str) -> Optional[dict]:
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"label": {"type": "string"}, "description": {"type": "string"}},
                        "required": ["label", "description"],
                    },
                    "minItems": len(decision.options),
                    "maxItems": len(decision.options),
                },
            },
            "required": ["title", "body", "options"],
        }
        prompt = {
            "role": "user",
            "content": (
                "Rewrite only the title, body, option labels and descriptions for a Pokemon sports-career event. "
                "Do not mention or infer numbers, probability, rewards or hidden outcomes. "
                f"Language: {'Spanish' if locale.lower().startswith('es') else 'English'}. "
                f"Immutable skeleton: {json.dumps(asdict(decision), ensure_ascii=False)}. "
                f"World context: {json.dumps(context, ensure_ascii=False)}."
            ),
        }
        body = json.dumps({"model": self.model, "messages": [prompt], "stream": False, "format": schema}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload.get("message", {}).get("content", "")
            return json.loads(content) if isinstance(content, str) else None
        except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
            return None

    def _read_cache(self, key: str) -> Optional[dict]:
        path = self.cache_root / f"{key}.json"
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        except (OSError, ValueError):
            return None

    def _write_cache(self, key: str, payload: dict) -> None:
        try:
            self.cache_root.mkdir(parents=True, exist_ok=True)
            path = self.cache_root / f"{key}.json"
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            temp.replace(path)
        except OSError:
            pass


def _mechanical_signature(decision: CareerDecision) -> str:
    mechanics = [
        {
            "id": option.id,
            "risk": option.risk,
            "transparency": option.transparency,
            "guaranteed": option.guaranteed,
            "gamble": option.gamble,
        }
        for option in decision.options
    ]
    return hashlib.sha256(json.dumps(mechanics, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _apply_prose(decision: CareerDecision, prose: dict) -> CareerDecision:
    decision.title = str(prose.get("title") or decision.title)[:160]
    decision.body = str(prose.get("body") or decision.body)[:1200]
    options = prose.get("options")
    if not isinstance(options, list) or len(options) != len(decision.options):
        return decision
    for option, generated in zip(decision.options, options):
        if isinstance(generated, dict):
            option.label = str(generated.get("label") or option.label)[:120]
            option.description = str(generated.get("description") or option.description)[:500]
    return decision
