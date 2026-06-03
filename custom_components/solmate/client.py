"""Minimal async client for the EET SolMate WebSocket API.

The protocol is taken from the official ``eet-energy/solmate-sdk``:
every request is a JSON frame ``{"route": ..., "id": ..., "data": ...}`` and
the server answers with either ``{"data": ...}`` or ``{"error": ...}``.

We deliberately do NOT use the official SDK package inside Home Assistant
because it manages its own asyncio event loop and writes an auth-token file to
disk. Instead we reuse Home Assistant's shared aiohttp client session, which
avoids event-loop conflicts and any extra dependency.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging

from aiohttp import ClientError, ClientSession, WSMsgType

_LOGGER = logging.getLogger(__name__)

CLOUD_URI = "wss://sol.eet.energy:9124"
DEFAULT_PORT = 9124
DEVICE_ID_LOCAL = "local_webinterface"
DEVICE_ID_CLOUD = "solmate-sdk"


class SolMateError(Exception):
    """Generic SolMate communication error."""


class SolMateAuthError(SolMateError):
    """Authentication (serial number / password) failed."""


class SolMateClient:
    """Lightweight async WebSocket client for a single SolMate."""

    def __init__(
        self,
        session: ClientSession,
        serial: str,
        password: str,
        uri: str,
        *,
        local: bool = True,
    ) -> None:
        self._session = session
        self._serial = serial
        self._password = password
        self._uri = uri
        self._local = local
        self._device_id = DEVICE_ID_LOCAL if local else DEVICE_ID_CLOUD
        self._ws = None
        self._token: str | None = None
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def _open(self, uri: str) -> None:
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        _LOGGER.debug("Connecting to SolMate at %s", uri)
        self._ws = await self._session.ws_connect(uri, heartbeat=20)

    async def _raw_request(self, route: str, data: dict, timeout: float = 30):
        assert self._ws is not None
        await self._ws.send_str(json.dumps({"route": route, "id": 1, "data": data}))
        msg = await self._ws.receive(timeout=timeout)
        if msg.type != WSMsgType.TEXT:
            raise SolMateError(f"Unexpected websocket frame: {msg.type}")
        resp = json.loads(msg.data)
        if "error" in resp:
            raise SolMateError(str(resp["error"]))
        return resp.get("data")

    async def connect(self) -> None:
        """Open the socket, log in and authenticate."""
        await self._open(self._uri)

        pw_hash = base64.encodebytes(
            hashlib.sha256(self._password.encode()).digest()
        ).decode()

        try:
            login = await self._raw_request(
                "login",
                {
                    "serial_num": self._serial,
                    "user_password_hash": pw_hash,
                    "device_id": self._device_id,
                },
            )
        except SolMateError as err:
            raise SolMateAuthError("Login failed (check serial number / password)") from err

        if not login or not login.get("success"):
            raise SolMateAuthError("Login rejected (check serial number / password)")
        self._token = login["signature"]

        auth = {
            "serial_num": self._serial,
            "signature": self._token,
            "device_id": self._device_id,
        }

        # In cloud mode the load balancer can redirect us to a specific node.
        if not self._local:
            info = await self._raw_request("authenticate", auth)
            redirect = (info or {}).get("redirect")
            if redirect and redirect != self._uri:
                _LOGGER.debug("Redirected to %s", redirect)
                self._uri = redirect
                await self._open(self._uri)

        await self._raw_request("authenticate", auth)
        _LOGGER.debug("SolMate %s authenticated", self._serial)

    async def request(self, route: str, data: dict | None = None, timeout: float = 30):
        """Serialised request with one transparent reconnect on a dropped socket."""
        async with self._lock:
            if not self.connected:
                await self.connect()
            try:
                return await self._raw_request(route, data or {}, timeout)
            except SolMateError:
                raise
            except (ClientError, asyncio.TimeoutError, ConnectionError) as err:
                _LOGGER.debug("Request %s failed (%s) - reconnecting", route, err)
                await self.connect()
                return await self._raw_request(route, data or {}, timeout)

    # --- reads -----------------------------------------------------------
    async def live_values(self) -> dict:
        return await self.request("live_values", {}) or {}

    async def injection_settings(self) -> dict:
        return await self.request("get_injection_settings", {}) or {}

    async def user_settings(self) -> dict:
        return await self.request("get_user_settings", {}) or {}

    # --- writes ----------------------------------------------------------
    async def set_min_injection(self, watts: int):
        return await self.request("set_user_minimum_injection", {"injection": int(watts)})

    async def set_max_injection(self, watts: int):
        return await self.request("set_user_maximum_injection", {"injection": int(watts)})

    async def set_min_battery_percentage(self, percentage: int):
        return await self.request(
            "set_user_minimum_battery_percentage", {"battery_percentage": int(percentage)}
        )

    async def set_boost_injection(self, seconds: int, watts: int):
        return await self.request(
            "set_boost_injection", {"time": int(seconds), "wattage": int(watts)}
        )

    async def close(self) -> None:
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        self._ws = None
