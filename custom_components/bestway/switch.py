"""Switch platform for Bestway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BestwayCoordinator


@dataclass(frozen=True)
class BestwaySwitchDescription:
    """Description of a Bestway switch."""

    key_v1: str
    key_v2: str
    name: str


SWITCHES = (
    BestwaySwitchDescription("filter_power", "filter", "Filter"),
    BestwaySwitchDescription("wave_power", "wave", "Bubbles"),
    BestwaySwitchDescription("heat_power", "heat", "Heater"),
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
        if self.entity_description.key_v2 in self._attrs:
            return self.entity_description.key_v2
        return self.entity_description.key_v1

    @property
    def _device_name(self) -> str:
        device = self._payload["device"]
        return device.get("dev_alias") or device.get("mac") or self._did

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{self._did}_{self.entity_description.name.lower()}"

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
        if self._key == "wave":
            return int(value) > 0
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        value = 100 if self._key == "wave" else 1
        await self.coordinator.async_send_command(self._did, self._key, value)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.async_send_command(self._did, self._key, 0)
