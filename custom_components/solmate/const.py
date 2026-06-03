"""Constants for the EET SolMate integration."""
from __future__ import annotations

DOMAIN = "solmate"
PLATFORMS = ["sensor", "number"]

CONF_SERIAL = "serial"
CONF_PASSWORD = "password"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 9124
DEFAULT_SCAN_INTERVAL = 10  # seconds

SERVICE_SET_BOOST = "set_boost"
