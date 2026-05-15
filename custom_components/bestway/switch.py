"""Switch platform for Bestway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BestwayCoordinator


@dataclass(frozen=True)
class BestwaySwitchDescription(SwitchEntityDescription):
    """Description of a Bestway switch.

    ``key`` is the attribute name used on newer (v2) firmware.
    ``key_fallback`` is the attribute name used on older (v1) firmware.
    """

    key_fallback: str = ""


SWITCHES = (
    BestwaySwitchDescription(key="filter", key_fallback="filter_power", name="Filter"),
    BestwaySwitchDescription(key="wave", key_fallback="wave_power", name="Bubbles"),
    BestwaySwitchDescription(key="heat", key_fallback="heat_power", name="Heater"),
    BestwaySwitchDescription(key="power", key_fallback="power", name="Power"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bestway switches."""
    coordinator: BestwayCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        BestwaySwitch(coordinator, did, desc)
        for did in coordinator.data
        for desc in SWITCHES
    ]
    async_add_entities(entities)


class BestwaySwitch(CoordinatorEntity[BestwayCoordinator], SwitchEntity):
    """Representation of a Bestway switch."""

    def __init__(
        self,
        coordinator: BestwayCoordinator,
        did: str,
        description: BestwaySwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self._did = did
        self.entity_description = description

    @property
    def _payload(self) -> dict[str, Any]:
        return self.coordinator.data[self._did]

    @property
    def _attrs(self) -> dict[str, Any]:
        return self._payload.get("attrs", {})

    @property
    def _key(self) -> str:
        """Return the attribute key to use for this device's firmware version."""
        if self.entity_description.key in self._attrs:
            return self.entity_description.key
        fallback = self.entity_description.key_fallback
        return fallback if fallback else self.entity_description.key

    @property
    def _device_name(self) -> str:
        device = self._payload["device"]
        return device.get("dev_alias") or device.get("mac") or self._did

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{self._did}_{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return entity name."""
        return f"{self._device_name} {self.entity_description.name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device metadata."""
        device = self._payload["device"]
        return DeviceInfo(
            identifiers={(DOMAIN, self._did)},
            manufacturer="Bestway",
            model=device.get("product_key"),
            name=self._device_name,
        )

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        value = self._attrs.get(self._key, 0)
        if self._key in ("wave", "wave_power"):
            return int(value) > 0
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        value = 100 if self._key in ("wave", "wave_power") else 1
        await self.coordinator.async_send_command(self._did, self._key, value)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.async_send_command(self._did, self._key, 0)
