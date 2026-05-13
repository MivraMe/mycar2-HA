from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_LOCK, CMD_UNLOCK, DOMAIN
from .coordinator import MyCar2Coordinator
from .entity import MyCar2Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MyCar2Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MyCar2Lock(coordinator)])


class MyCar2Lock(MyCar2Entity, LockEntity):
    _attr_translation_key = "doors_lock"

    def __init__(self, coordinator: MyCar2Coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.vehicle_id}_lock"

    @property
    def is_locked(self) -> bool | None:
        return self.coordinator.data.get("status", {}).get("Status_Lock")

    async def async_lock(self, **kwargs) -> None:
        status = self.coordinator.data.get("status") if self.coordinator.data else None
        await self.coordinator.api.awake_and_command(self.coordinator.vehicle_id, CMD_LOCK, status)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs) -> None:
        status = self.coordinator.data.get("status") if self.coordinator.data else None
        await self.coordinator.api.awake_and_command(self.coordinator.vehicle_id, CMD_UNLOCK, status)
        await self.coordinator.async_request_refresh()
