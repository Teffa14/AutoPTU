"""Thread-safe WebSocket fan-out for persistent campaign events."""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Set, Tuple


Subscription = Tuple[asyncio.AbstractEventLoop, asyncio.Queue]


@dataclass
class CampaignRealtimeHub:
    subscriptions: Dict[str, Set[Subscription]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def subscribe(self, campaign_id: str) -> Subscription:
        subscription = (asyncio.get_running_loop(), asyncio.Queue(maxsize=256))
        with self._lock:
            self.subscriptions.setdefault(campaign_id, set()).add(subscription)
        return subscription

    def unsubscribe(self, campaign_id: str, subscription: Subscription) -> None:
        with self._lock:
            listeners = self.subscriptions.get(campaign_id)
            if listeners is None:
                return
            listeners.discard(subscription)
            if not listeners:
                self.subscriptions.pop(campaign_id, None)

    def publish(self, campaign_id: str, event: Dict[str, Any]) -> None:
        with self._lock:
            listeners = list(self.subscriptions.get(campaign_id, set()))
        # Fan-out is an invalidation signal only. Subscribers fetch a fresh
        # role-redacted snapshot, so secret command details cannot cross seats.
        message = {
            "type": "campaign.event",
            "campaign_id": campaign_id,
            "event": {"seq": int(event.get("seq") or 0), "type": "campaign.updated"},
        }
        for loop, queue in listeners:
            def deliver(target: asyncio.Queue = queue, payload: Dict[str, Any] = message) -> None:
                if target.full():
                    try:
                        target.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                target.put_nowait(payload)

            if not loop.is_closed():
                loop.call_soon_threadsafe(deliver)


__all__ = ["CampaignRealtimeHub", "Subscription"]
