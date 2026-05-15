"""Sensor platform for Bestway."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BestwayCoordinator


@dataclass(frozen=True)
class BestwaySensorDescription:
    """Description of a Bestway sensor."""

    key: str
    name: str
    device_class: SensorDeviceClass | None = None
    native_unit: str | None = None
    state_class: SensorStateClass | None = None


SENSORS = (
    BestwaySensorDescription(
        key="temp_now",
        name="Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BestwaySensorDescription(
        key="updated_at",
        name="Last Update",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bestway sensors."""
    coordinator: BestwayCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        BestwaySensor(coordinator, did, desc)
        for did in coordinator.data
        for desc in SENSORS
    ]
    async_add_entities(entities)


class BestwaySensor(CoordinatorEntity[BestwayCoordinator], SensorEntity):
    """Representation of a Bestway sensor."""

    def __init__(
        self,
        coordinator: BestwayCoordinator,
        did: str,
        description: BestwaySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._did = did
        self.entity_description = description
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.native_unit
        self._attr_state_class = description.state_class

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
    def native_value(self) -> Any:
        """Return sensor value."""
        if self.entity_description.key == "updated_at":
            timestamp = self._payload.get("updated_at")
            if timestamp is None:
                return None
            return datetime.fromtimestamp(int(timestamp), tz=UTC)

        return self._attrs.get(self.entity_description.key)
