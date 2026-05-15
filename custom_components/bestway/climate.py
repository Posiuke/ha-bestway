"""Climate platform for Bestway."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BestwayCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bestway climate entities."""
    coordinator: BestwayCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [BestwayClimate(coordinator, did) for did in coordinator.data]
    async_add_entities(entities)


class BestwayClimate(CoordinatorEntity[BestwayCoordinator], ClimateEntity):
    """Representation of a Bestway spa climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_min_temp = 20
    _attr_max_temp = 40

    def __init__(self, coordinator: BestwayCoordinator, did: str) -> None:
        super().__init__(coordinator)
        self._did = did

    @property
    def _payload(self) -> dict[str, Any]:
        return self.coordinator.data[self._did]

    @property
    def _attrs(self) -> dict[str, Any]:
        return self._payload.get("attrs", {})

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return f"{self._did}_climate"

    @property
    def name(self) -> str:
        """Return entity name."""
        return f"{self._device_name} Climate"

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
    def _device_name(self) -> str:
        device = self._payload["device"]
        return device.get("dev_alias") or device.get("mac") or self._did

    @property
    def current_temperature(self) -> float | None:
        """Return current water temperature."""
        value = self._attrs.get("temp_now")
        return float(value) if value is not None else None

    @property
    def target_temperature(self) -> float | None:
        """Return target temperature."""
        value = self._attrs.get("Tset", self._attrs.get("temp_set"))
        return float(value) if value is not None else None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        power = self._attrs.get("power", 0)
        heat = self._attrs.get("heat", self._attrs.get("heat_power", 0))

        if not power:
            return HVACMode.OFF
        if heat:
            return HVACMode.HEAT
        return HVACMode.FAN_ONLY

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        heat_key = "heat" if "heat" in self._attrs else "heat_power"

        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_send_command(self._did, "power", 0)
            return

        await self.coordinator.async_send_command(self._did, "power", 1)

        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.async_send_command(self._did, heat_key, 1)
        elif hvac_mode == HVACMode.FAN_ONLY:
            await self.coordinator.async_send_command(self._did, heat_key, 0)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        command = "Tset" if "Tset" in self._attrs else "temp_set"
        await self.coordinator.async_send_command(self._did, command, int(temperature))
