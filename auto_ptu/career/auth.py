from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CareerIdentity:
    user_id: str
    permanent: bool
    source: str


class SupabaseIdentityResolver:
    """Resolve a Supabase access token without exposing a service-role key."""

    def resolve(self, authorization: str = "", development_user: str = "") -> CareerIdentity:
        token = _bearer(authorization)
        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        publishable = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
        if token and url and publishable:
            request = Request(
                f"{url}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}", "apikey": publishable},
            )
            try:
                with urlopen(request, timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                raise PermissionError("Supabase session validation failed.") from exc
            user_id = str(payload.get("id") or "").strip()
            if not user_id:
                raise PermissionError("Supabase did not return a user identity.")
            anonymous = bool(payload.get("is_anonymous"))
            return CareerIdentity(user_id=user_id, permanent=not anonymous, source="supabase")
        if development_user:
            return CareerIdentity(user_id=str(development_user), permanent=True, source="development")
        guest = token or "guest-local"
        return CareerIdentity(user_id=f"guest-{guest[-16:]}", permanent=False, source="guest")


def _bearer(value: str) -> str:
    text = str(value or "").strip()
    return text[7:].strip() if text.lower().startswith("bearer ") else text
