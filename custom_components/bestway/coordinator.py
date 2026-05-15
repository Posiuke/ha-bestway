"""Data update coordinator for Bestway."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BestwayApi, BestwayApiError
from .const import POLL_INTERVAL, TOKEN_REFRESH_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BestwayCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinate Bestway cloud updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: BestwayApi,
        username: str,
        password: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Bestway",
            update_interval=POLL_INTERVAL,
        )
        self.api = api
        self._username = username
        self._password = password
        self._last_login: datetime | None = None

    async def async_login(self) -> str:
        """Login and update token timestamp."""
        uid = await self.api.async_login(self._username, self._password)
        self._last_login = datetime.now(UTC)
        return uid

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch all devices and their current state."""
        try:
            await self._async_ensure_auth()
            devices = await self.api.async_get_devices()
            data: dict[str, dict[str, Any]] = {}

            for device in devices:
                did = device.get("did")
                if not did:
                    continue
                status = await self.api.async_get_device_status(did)
                data[did] = {
                    "device": device,
                    "attrs": status.get("attr", {}),
                    "updated_at": status.get("updated_at"),
                }

            return data
        except BestwayApiError as err:
            raise UpdateFailed(f"Failed to fetch Bestway data: {err}") from err

    async def async_send_command(self, did: str, command: str, value: Any) -> None:
        """Send command and request immediate refresh."""
        if did not in self.data:
            raise UpdateFailed(f"Device {did} not found")

        payload = self.data[did]
        await self.api.async_control(
            payload["device"],
            did,
            command,
            value,
            payload.get("attrs", {}),
        )
        await asyncio.sleep(5)
        await self.async_request_refresh()

    async def _async_ensure_auth(self) -> None:
        """Ensure token exists and is refreshed every 7 days."""
        now = datetime.now(UTC)
        if not self.api.token or not self._last_login:
            await self.async_login()
            return

        if now - self._last_login >= TOKEN_REFRESH_INTERVAL:
            await self.async_login()
