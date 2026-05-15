"""Binary sensor platform for Bestway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BestwayCoordinator


@dataclass(frozen=True)
class BestwayBinarySensorDescription:
    """Description of a Bestway binary sensor."""

    key: str
    name: str
    device_class: BinarySensorDeviceClass


BINARY_SENSORS = [
    BestwayBinarySensorDescription(
        key="heat_temp_reach",
        name="Target Temperature Reached",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    BestwayBinarySensorDescription(
        key="locked",
        name="Panel Locked",
        device_class=BinarySensorDeviceClass.LOCK,
    ),
    BestwayBinarySensorDescription(
        key="earth",
        name="Earth Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
]
BINARY_SENSORS.extend(
    BestwayBinarySensorDescription(
        key=f"system_err{index}",
        name=f"System Error {index}",
        device_class=BinarySensorDeviceClass.PROBLEM,
    )
    for index in range(1, 10)
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bestway binary sensors."""
    coordinator: BestwayCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        BestwayBinarySensor(coordinator, did, desc)
        for did in coordinator.data
        for desc in BINARY_SENSORS
    ]
    async_add_entities(entities)


class BestwayBinarySensor(CoordinatorEntity[BestwayCoordinator], BinarySensorEntity):
    """Representation of a Bestway binary sensor."""

    def __init__(
        self,
        coordinator: BestwayCoordinator,
        did: str,
        description: BestwayBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._did = did
        self.entity_description = description
        self._attr_device_class = description.device_class

    @property
    def _payload(self) -> dict[str, Any]:
        return self.coordinator.data[self._did]

    @property
    def _attrs(self) -> dict[str, Any]:
        return self._payload.get("attrs", {})

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
        """Return true if active/problem state is set."""
        return bool(self._attrs.get(self.entity_description.key, 0))
