"""The Bestway integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BestwayApi, BestwayApiError
from .const import CONF_REGION, DOMAIN, PLATFORMS
from .coordinator import BestwayCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bestway from a config entry."""
    session = async_get_clientsession(hass)
    api = BestwayApi(session, entry.data[CONF_REGION])
    coordinator = BestwayCoordinator(
        hass,
        api,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    try:
        await coordinator.async_login()
        await coordinator.async_config_entry_first_refresh()
    except BestwayApiError as err:
        raise ConfigEntryNotReady(f"Unable to connect to Bestway API: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
