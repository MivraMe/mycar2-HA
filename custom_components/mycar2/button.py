from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CMD_EXTEND,
    CMD_PANIC_OFF,
    CMD_PANIC_ON,
    CMD_REFRESH_RS,
    CMD_START,
    CMD_STOP,
    CMD_TRUNK,
    CMD_VALET,
    DOMAIN,
)
from .coordinator import MyCar2Coordinator
from .entity import MyCar2Entity


@dataclass(frozen=True, kw_only=True)
class MyCar2ButtonDescription(ButtonEntityDescription):
    command: int = 0
    use_awake: bool = True


BUTTONS: tuple[MyCar2ButtonDescription, ...] = (
    MyCar2ButtonDescription(key="start", translation_key="start", command=CMD_START),
    MyCar2ButtonDescription(key="stop", translation_key="stop", command=CMD_STOP),
    MyCar2ButtonDescription(key="extend", translation_key="extend", command=CMD_EXTEND),
    MyCar2ButtonDescription(key="trunk", translation_key="trunk_release", command=CMD_TRUNK),
    MyCar2ButtonDescription(key="panic_on", translation_key="panic_on", command=CMD_PANIC_ON, use_awake=False),
    MyCar2ButtonDescription(key="panic_off", translation_key="panic_off", command=CMD_PANIC_OFF, use_awake=False),
    MyCar2ButtonDescription(key="valet", translation_key="valet", command=CMD_VALET, use_awake=False),
    MyCar2ButtonDescription(
        key="refresh",
        translation_key="refresh",
        command=CMD_REFRESH_RS,
        use_awake=False,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: MyCar2Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MyCar2Button(coordinator, desc) for desc in BUTTONS)


class MyCar2Button(MyCar2Entity, ButtonEntity):
    entity_description: MyCar2ButtonDescription

    def __init__(
        self, coordinator: MyCar2Coordinator, description: MyCar2ButtonDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.vehicle_id}_{description.key}"

    async def async_press(self) -> None:
        status = self.coordinator.data.get("status") if self.coordinator.data else None
        if self.entity_description.use_awake:
            await self.coordinator.api.awake_and_command(
                self.coordinator.vehicle_id, self.entity_description.command, status
            )
        else:
            await self.coordinator.api.send_command(
                self.coordinator.vehicle_id, self.entity_description.command
            )
        await self.coordinator.async_request_refresh()
