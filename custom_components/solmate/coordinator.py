import asyncio
import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SolMateCoordinator(DataUpdateCoordinator):
    """Coordinator for SolMate integration."""

    def __init__(self, hass, host, port):
        """Initialize coordinator."""

        self.host = host
        self.port = port

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )

        self._connected = False
        self._client = None  # später websocket/api client

    async def _async_update_data(self):
        """
        Central data update point (called by HA scheduler).
        Must NEVER block indefinitely.
        """

        try:
            # -----------------------------
            # 1. Ensure connection
            # -----------------------------
            if not self._connected:
                await self._connect()

            # -----------------------------
            # 2. Fetch data
            # -----------------------------
            data = await self._fetch_data()

            return data

        except Exception as err:
            _LOGGER.error("SolMate update failed: %s", err)
            raise UpdateFailed(err) from err

    async def _connect(self):
        """Connect to SolMate API / Websocket."""

        _LOGGER.info("Connecting to SolMate at %s:%s", self.host, self.port)

        # TODO: hier deine echte websocket/mqtt/api init
        await asyncio.sleep(0.2)  # placeholder non-blocking init

        self._connected = True

        _LOGGER.info("SolMate connected")

    async def _fetch_data(self):
        """Fetch latest values from SolMate."""

        # TODO: hier echte API / websocket read
        await asyncio.sleep(0.1)

        # Dummy structure (ersetzen durch echte Daten)
        return {
            "power": 1234,
            "status": "online",
        }

    async def start(self):
        """
        Optional compatibility layer (for old calls).
        Now SAFE: does NOT block setup anymore.
        """
        if not self._connected:
            await self._connect()

    async def stop(self):
        """Cleanup."""

        _LOGGER.info("Stopping SolMate coordinator")

        self._connected = False

        # TODO: websocket close / mqtt disconnect etc.
        self._client = None
