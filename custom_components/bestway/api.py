"""Gizwits API client for Bestway spas."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession

from .const import APP_ID, APP_KEY_V2, CONTROL_V2_URL


class BestwayApiError(Exception):
    """Raised when the API returns an error."""


class BestwayAuthError(BestwayApiError):
    """Raised when authentication fails."""


class BestwayApi:
    """Async client for Bestway Gizwits API."""

    def __init__(self, session: ClientSession, region: str) -> None:
        self._session = session
        self._base_url = f"https://{region}.gizwits.com"
        self._token: str | None = None
        self._uid: str | None = None

    @property
    def uid(self) -> str | None:
        """Return current user id."""
        return self._uid

    @property
    def token(self) -> str | None:
        """Return current user token."""
        return self._token

    async def async_login(self, username: str, password: str) -> str:
        """Authenticate and return uid."""
        payload = {"username": username, "password": password, "lang": "en"}
        try:
            async with self._session.post(
                f"{self._base_url}/app/login",
                headers={"X-Gizwits-Application-Id": APP_ID},
                json=payload,
            ) as resp:
                data = await resp.json(content_type=None)
        except (ClientError, ValueError) as err:
            raise BestwayApiError("Login request failed") from err

        token = data.get("token")
        uid = data.get("uid")
        if not token or not uid:
            raise BestwayAuthError(data.get("error_message", "Invalid credentials"))

        self._token = token
        self._uid = uid
        return uid

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Get user-bound devices."""
        data = await self._api_get("/app/bindings?show_disabled=0&limit=20&skip=0")
        return data.get("devices", [])

    async def async_get_device_status(self, did: str) -> dict[str, Any]:
        """Get latest device attributes."""
        return await self._api_get(f"/app/devdata/{did}/latest")

    async def async_control(
        self,
        device: dict[str, Any],
        did: str,
        command: str,
        value: Any,
        attrs: dict[str, Any],
    ) -> None:
        """Send control command using v1 or v2 endpoint based on device attrs."""
        if command in {"Tset", "heat", "filter", "jet", "wave"} or any(
            key in attrs for key in ("Tset", "heat", "filter", "jet", "wave")
        ):
            await self._control_v2(device, command, value)
            return

        await self._api_post(f"/app/control/{did}", {"attrs": {command: value}})

    async def _control_v2(self, device: dict[str, Any], command: str, value: Any) -> None:
        """Send command to v2 control endpoint."""
        if not self._token or not self._uid:
            raise BestwayAuthError("Missing token")

        payload = {
            "appKey": APP_KEY_V2,
            "type": "appId",
            "version": "1.0",
            "data": {
                "command": {command: value},
                "did": device["did"],
                "mac": device["mac"],
                "productKey": device["product_key"],
                "uid": self._uid,
            },
        }

        headers = {
            "Authorization": self._token,
            "Version": "1.0",
            "Content-Type": "application/json",
        }

        try:
            async with self._session.post(CONTROL_V2_URL, headers=headers, json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise BestwayApiError(data.get("msg", "Control v2 failed"))
        except (ClientError, ValueError) as err:
            raise BestwayApiError("Control v2 request failed") from err

    async def _api_get(self, path: str) -> dict[str, Any]:
        """Perform authenticated GET request."""
        headers = self._headers()
        try:
            async with self._session.get(f"{self._base_url}{path}", headers=headers) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise BestwayApiError(data.get("error_message", "API GET failed"))
        except (ClientError, ValueError) as err:
            raise BestwayApiError("API GET request failed") from err
        return data

    async def _api_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Perform authenticated POST request."""
        headers = self._headers()
        try:
            async with self._session.post(
                f"{self._base_url}{path}",
                headers=headers,
                json=payload,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise BestwayApiError(data.get("error_message", "API POST failed"))
        except (ClientError, ValueError) as err:
            raise BestwayApiError("API POST request failed") from err
        return data

    def _headers(self) -> dict[str, str]:
        """Return authenticated headers."""
        if not self._token:
            raise BestwayAuthError("Not authenticated")
        return {
            "X-Gizwits-Application-Id": APP_ID,
            "X-Gizwits-User-token": self._token,
            "Content-Type": "application/json",
        }
