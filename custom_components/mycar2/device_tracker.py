from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import MyCar2Coordinator
from .entity import MyCar2Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MyCar2Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MyCar2DeviceTracker(coordinator)])


class MyCar2DeviceTracker(MyCar2Entity, TrackerEntity):
    _attr_translation_key = "tracker"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: MyCar2Coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.vehicle_id}_tracker"

    @property
    def latitude(self) -> float | None:
        pos = self.coordinator.data.get("position", {}) if self.coordinator.data else {}
        lat = pos.get("Latitude")
        return float(lat) if lat is not None else None

    @property
    def longitude(self) -> float | None:
        pos = self.coordinator.data.get("position", {}) if self.coordinator.data else {}
        lon = pos.get("Longitude")
        return float(lon) if lon is not None else None

    @property
    def location_accuracy(self) -> int:
        return 10

    @property
    def extra_state_attributes(self) -> dict:
        pos = self.coordinator.data.get("position", {}) if self.coordinator.data else {}
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return {
            "altitude": pos.get("Altitude"),
            "heading": pos.get("Heading"),
            "speed": pos.get("Speed") or status.get("GpsSpeed"),
        }
