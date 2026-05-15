"""Config flow for Bestway integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BestwayApi, BestwayApiError
from .const import API_REGIONS, CONF_REGION, DEFAULT_REGION, DOMAIN


class BestwayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bestway."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = BestwayApi(session, user_input[CONF_REGION])

            try:
                uid = await api.async_login(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_USERNAME], data=user_input)
            except BestwayApiError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(API_REGIONS),
                }
            ),
            errors=errors,
        )
