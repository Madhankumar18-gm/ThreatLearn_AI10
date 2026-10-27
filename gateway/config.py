"""
ThreatLens Gateway Configuration (Phase 1A).

Configures local loopback ports, frame constraints, subprotocols,
and timeout parameters for the independent OCPP 1.6-J gateway proxy.
"""

from dataclasses import dataclass, field
import os
from typing import List

from gateway.policy import PolicyConfig


@dataclass
class GatewayConfig:
    """Configuration settings for the ThreatLens OCPP Security Gateway."""

    # Loopback network interface
    host: str = "127.0.0.1"
    charger_port: int = 9000      # Charger connects here: ws://127.0.0.1:9000/{cp_id}
    csms_host: str = "127.0.0.1"
    csms_port: int = 9001         # Gateway forwards upstream to: ws://127.0.0.1:9001/{cp_id}

    # Framing limits
    max_frame_bytes: int = 65536  # Strict 64 KB per frame limit (RFC 6455 policy violation above)
    subprotocols: List[str] = field(default_factory=lambda: ["ocpp1.6"])

    # Timing & correlation
    call_timeout_seconds: float = 10.0
    prune_interval_seconds: float = 30.0

    # WebSocket connection lifecycle
    ping_interval: float = 20.0
    ping_timeout: float = 10.0
    close_timeout: float = 5.0

    # Deterministic Policy Configuration
    policy: PolicyConfig = field(default_factory=PolicyConfig)

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        """Instantiate configuration from environment variables with safe defaults."""
        return cls(
            host=os.getenv("THREATLENS_GATEWAY_HOST", "127.0.0.1"),
            charger_port=int(os.getenv("THREATLENS_CHARGER_PORT", "9000")),
            csms_host=os.getenv("THREATLENS_CSMS_HOST", "127.0.0.1"),
            csms_port=int(os.getenv("THREATLENS_CSMS_PORT", "9001")),
            max_frame_bytes=int(os.getenv("THREATLENS_MAX_FRAME_BYTES", "65536")),
            call_timeout_seconds=float(os.getenv("THREATLENS_CALL_TIMEOUT", "10.0")),
            ping_interval=float(os.getenv("THREATLENS_PING_INTERVAL", "20.0")),
            ping_timeout=float(os.getenv("THREATLENS_PING_TIMEOUT", "10.0")),
            close_timeout=float(os.getenv("THREATLENS_CLOSE_TIMEOUT", "5.0")),
        )
