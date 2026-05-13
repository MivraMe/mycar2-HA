import asyncio

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CMD_LOCK, CMD_UNLOCK, DOMAIN
from .coordinator import MyCar2Coordinator
from .entity import MyCar2Entity

# Seconds to wait after a command before polling, giving the device time to process.
_COMMAND_SETTLE = 2


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
        # Initialise from whatever data is already available.
        self._attr_is_locked = self._status_lock()

    def _status_lock(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("status", {}).get("Status_Lock")

    def _handle_coordinator_update(self) -> None:
        """Sync real state from coordinator; clears any optimistic value."""
        value = self._status_lock()
        if value is not None:
            self._attr_is_locked = value
        super()._handle_coordinator_update()

    async def async_lock(self, **kwargs) -> None:
        status = self.coordinator.data.get("status") if self.coordinator.data else None
        await self.coordinator.api.awake_and_command(self.coordinator.vehicle_id, CMD_LOCK, status)
        # Optimistic: reflect the expected state immediately in the UI.
        self._attr_is_locked = True
        self.async_write_ha_state()
        await asyncio.sleep(_COMMAND_SETTLE)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs) -> None:
        status = self.coordinator.data.get("status") if self.coordinator.data else None
        await self.coordinator.api.awake_and_command(self.coordinator.vehicle_id, CMD_UNLOCK, status)
        self._attr_is_locked = False
        self.async_write_ha_state()
        await asyncio.sleep(_COMMAND_SETTLE)
        await self.coordinator.async_request_refresh()
