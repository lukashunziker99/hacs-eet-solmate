"""Config flow for the EET SolMate integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import CLOUD_URI, SolMateAuthError, SolMateClient, SolMateError
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SERIAL,
    DEFAULT_PORT,
    DOMAIN,
)


class SolMateConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the SolMate config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            serial = user_input[CONF_SERIAL].strip()
            host = (user_input.get(CONF_HOST) or "").strip()
            local = bool(host)
            uri = (
                f"ws://{host}:{user_input.get(CONF_PORT, DEFAULT_PORT)}/"
                if local
                else CLOUD_URI
            )

            client = SolMateClient(
                async_get_clientsession(self.hass),
                serial,
                user_input[CONF_PASSWORD],
                uri,
                local=local,
            )
            try:
                await client.connect()
                await client.live_values()
            except SolMateAuthError:
                errors["base"] = "invalid_auth"
            except SolMateError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

            if not errors:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"SolMate {serial}",
                    data={
                        CONF_SERIAL: serial,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_HOST: host,
                        CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_SERIAL): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_HOST, default=""): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
