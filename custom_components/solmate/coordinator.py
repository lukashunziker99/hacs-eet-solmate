"""DataUpdateCoordinator for the EET SolMate integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CLOUD_URI, SolMateAuthError, SolMateClient, SolMateError
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SolMateCoordinator(DataUpdateCoordinator):
    """Coordinates polling for one SolMate device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        data = entry.data

        host = (data.get(CONF_HOST) or "").strip()
        local = bool(host)
        if local:
            uri = f"ws://{host}:{data.get(CONF_PORT, DEFAULT_PORT)}/"
        else:
            uri = CLOUD_URI

        self.client = SolMateClient(
            async_get_clientsession(hass),
            data[CONF_SERIAL],
            data[CONF_PASSWORD],
            uri,
            local=local,
        )

        scan = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan),
        )

    async def _async_update_data(self) -> dict:
        try:
            live = await self.client.live_values()
        except SolMateAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except SolMateError as err:
            raise UpdateFailed(str(err)) from err
        except Exception as err:  # noqa: BLE001 - surface as a clean update failure
            raise UpdateFailed(str(err)) from err

        result: dict = {"live": live}

        # Settings are optional / firmware-dependent: never fail the whole
        # update if one of them is unsupported.
        for name, coro in (
            ("injection", self.client.injection_settings),
            ("user", self.client.user_settings),
        ):
            try:
                result[name] = await coro()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not fetch %s settings: %s", name, err)
                result[name] = {}

        return result

    async def async_shutdown(self) -> None:
        await super().async_shutdown()
        await self.client.close()
