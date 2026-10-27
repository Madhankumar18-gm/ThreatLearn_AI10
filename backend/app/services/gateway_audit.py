"""
ThreatLens Non-Blocking Gateway Audit Service.

Buffers and records gateway decisions (ALLOW, CLAMP, BLOCK) in a bounded,
thread-safe ring-buffer. Operates decoupled from WebSocket message delivery
loops to guarantee zero latency penalty and visible dropped-event counts.
"""

from collections import deque
import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ThreatLens.Gateway.Audit")


class GatewayAuditService:
    """Non-blocking in-memory audit store with bounded queue depth."""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self._buffer: deque = deque(maxlen=capacity)
        self._lock = threading.Lock()
        self.total_events: int = 0
        self.delivered_events: int = 0
        self.dropped_events: int = 0

    def record_event(self, event: Dict[str, Any]) -> None:
        """
        Record a gateway policy decision. Non-blocking and exception-safe.
        """
        try:
            with self._lock:
                self.total_events += 1
                if len(self._buffer) >= self.capacity:
                    # Dropped oldest event due to buffer overflow
                    self.dropped_events += 1
                self._buffer.append(event)
                self.delivered_events += 1
        except Exception as exc:
            logger.warning("Audit record exception: %s", exc)

    def get_events(
        self,
        limit: int = 100,
        decision_filter: Optional[str] = None,
        rule_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent events in reverse chronological order."""
        with self._lock:
            events = list(self._buffer)

        # Reverse for newest first
        events.reverse()

        filtered: List[Dict[str, Any]] = []
        for e in events:
            if decision_filter and e.get("decision", "").upper() != decision_filter.upper():
                continue
            if rule_filter and rule_filter.upper() not in e.get("rule_id", "").upper():
                continue
            filtered.append(e)
            if len(filtered) >= limit:
                break

        return filtered

    def get_metrics(self) -> Dict[str, int]:
        """Return audit queue telemetry."""
        with self._lock:
            return {
                "total_events": self.total_events,
                "delivered_events": self.delivered_events,
                "dropped_events": self.dropped_events,
                "queue_capacity": self.capacity,
                "queue_depth": len(self._buffer),
            }

    def clear(self) -> None:
        """Reset the audit buffer."""
        with self._lock:
            self._buffer.clear()
            self.total_events = 0
            self.delivered_events = 0
            self.dropped_events = 0


# Shared singleton instance
gateway_audit_service = GatewayAuditService(capacity=1000)
