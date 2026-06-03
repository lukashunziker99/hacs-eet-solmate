"""Services for the EET SolMate integration."""
from __future__ import annotations

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN, SERVICE_SET_BOOST

SET_BOOST_SCHEMA = vol.Schema(
    {
        vol.Required("wattage"): cv.positive_int,
        vol.Optional("time", default=900): cv.positive_int,
    }
)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services (once)."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_BOOST):
        return

    async def _async_set_boost(call: ServiceCall) -> None:
        wattage = call.data["wattage"]
        seconds = call.data["time"]
        for coordinator in hass.data.get(DOMAIN, {}).values():
            await coordinator.client.set_boost_injection(seconds, wattage)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_BOOST, _async_set_boost, schema=SET_BOOST_SCHEMA
    )


def async_unload_services(hass: HomeAssistant) -> None:
    hass.services.async_remove(DOMAIN, SERVICE_SET_BOOST)
