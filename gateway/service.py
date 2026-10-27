"""
ThreatLens Gateway Service (Phase 1A).

Standalone execution entrypoint for the ThreatLens OCPP 1.6-J Security Gateway.
Usage:
    python -m gateway.service
    python -m gateway.service --charger-port 9000 --csms-port 9001
"""

import argparse
import asyncio
import logging
import signal
import sys
from typing import Optional

from gateway.config import GatewayConfig
from gateway.proxy import GatewayProxy


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging for ThreatLens Gateway."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] [ThreatLens.Gateway] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("ThreatLens.Gateway")


async def run_gateway(config: GatewayConfig) -> None:
    """Run the ThreatLens Gateway proxy until a shutdown signal is received."""
    logger = setup_logging()

    logger.info("=================================================================")
    logger.info(" ThreatLens OCPP Security Gateway (Phase 1A: Core & Framing)    ")
    logger.info(" Interface:      ws://%s:%d (Charger endpoint)", config.host, config.charger_port)
    logger.info(" Upstream CSMS:  ws://%s:%d (Central System endpoint)", config.csms_host, config.csms_port)
    logger.info(" Max Frame Size: %d bytes (64 KB limit)", config.max_frame_bytes)
    logger.info(" Subprotocols:   %s", config.subprotocols)
    logger.info(" Operating Mode: ALLOW (Phase 1A Transparent Framing Pass-Through)")
    logger.info(" Machine Learn.: STRICTLY NONE (100%% Deterministic Rules Only)   ")
    logger.info("=================================================================")

    proxy = GatewayProxy(config)
    await proxy.start()

    shutdown_event = asyncio.Event()

    def _trigger_shutdown(sig_name: str) -> None:
        logger.info("Received %s signal, initiating graceful shutdown...", sig_name)
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    # Windows loop signal registration
    try:
        loop.add_signal_handler(signal.SIGINT, lambda: _trigger_shutdown("SIGINT"))
        loop.add_signal_handler(signal.SIGTERM, lambda: _trigger_shutdown("SIGTERM"))
    except (NotImplementedError, AttributeError):
        # Fallback for Windows platform signal handler
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, lambda s, f: _trigger_shutdown(signal.Signals(s).name))
            except Exception:
                pass

    try:
        await shutdown_event.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Keyboard interrupt received.")
    finally:
        logger.info("Stopping ThreatLens Gateway proxy...")
        await proxy.stop()
        logger.info("ThreatLens Gateway proxy shutdown complete.")


def parse_args() -> GatewayConfig:
    """Parse CLI options with fallback to environment variables and defaults."""
    parser = argparse.ArgumentParser(
        description="ThreatLens OCPP 1.6-J Security Gateway (Phase 1A)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host binding address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--charger-port",
        type=int,
        default=None,
        help="Port on which EV chargers connect (default: 9000)",
    )
    parser.add_argument(
        "--csms-host",
        type=str,
        default=None,
        help="Host of the upstream CSMS (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--csms-port",
        type=int,
        default=None,
        help="Port of the upstream CSMS (default: 9001)",
    )
    parser.add_argument(
        "--max-frame-bytes",
        type=int,
        default=None,
        help="Maximum allowed frame size in bytes (default: 65536)",
    )
    parser.add_argument(
        "--call-timeout",
        type=float,
        default=None,
        help="Timeout in seconds for in-flight CALL requests (default: 10.0)",
    )

    args = parser.parse_args()
    config = GatewayConfig.from_env()

    if args.host:
        config.host = args.host
    if args.charger_port:
        config.charger_port = args.charger_port
    if args.csms_host:
        config.csms_host = args.csms_host
    if args.csms_port:
        config.csms_port = args.csms_port
    if args.max_frame_bytes:
        config.max_frame_bytes = args.max_frame_bytes
    if args.call_timeout:
        config.call_timeout_seconds = args.call_timeout

    return config


def main() -> None:
    config = parse_args()
    try:
        asyncio.run(run_gateway(config))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
