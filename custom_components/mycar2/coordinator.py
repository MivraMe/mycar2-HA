import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MyCar2ApiClient
from .const import API_BASE_URL, CMD_REFRESH_RS, DOMAIN, KEYFOB_SYNC_INTERVAL, POLL_INTERVAL
from .signalr import SignalRClient

_LOGGER = logging.getLogger(__name__)


class MyCar2Coordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        api: MyCar2ApiClient,
        vehicle_id: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{vehicle_id}",
            update_interval=timedelta(seconds=POLL_INTERVAL),
        )
        self.api = api
        self.vehicle_id = vehicle_id
        self.vehicle_info = vehicle_info
        self._signalr_task: asyncio.Task | None = None
        self._keyfob_task: asyncio.Task | None = None

    async def _async_update_data(self) -> dict:
        try:
            status_result, position_result = await asyncio.gather(
                self.api.get_vehicle_status(self.vehicle_id),
                self.api.get_vehicle_position(self.vehicle_id),
                return_exceptions=True,
            )
        except Exception as err:
            raise UpdateFailed(f"API communication error: {err}") from err

        current = self.data or {}

        if isinstance(status_result, Exception):
            _LOGGER.warning("Status fetch failed: %s", status_result)
            status = current.get("status", {})
        else:
            status = status_result

        if isinstance(position_result, Exception):
            _LOGGER.warning("Position fetch failed: %s", position_result)
            position = current.get("position", {})
        else:
            position = position_result

        return {"status": status, "position": position}

    def start_background_tasks(self) -> None:
        self._signalr_task = self.hass.async_create_background_task(
            self._signalr_loop(), f"mycar2_signalr_{self.vehicle_id}"
        )
        self._keyfob_task = self.hass.async_create_background_task(
            self._keyfob_sync_loop(), f"mycar2_keyfob_{self.vehicle_id}"
        )

    def stop_background_tasks(self) -> None:
        if self._signalr_task:
            self._signalr_task.cancel()
        if self._keyfob_task:
            self._keyfob_task.cancel()

    async def _signalr_loop(self) -> None:
        session = async_get_clientsession(self.hass)
        client = SignalRClient(API_BASE_URL, self.vehicle_id)
        while True:
            try:
                _LOGGER.debug("Opening SignalR connection for vehicle %s", self.vehicle_id)
                await self.api.ensure_token()
                async for payload in client.stream(session, self.api.id_token):
                    if self.data:
                        merged_status = {**self.data.get("status", {}), **payload}
                        self.async_set_updated_data({**self.data, "status": merged_status})
            except asyncio.CancelledError:
                return
            except Exception as err:
                _LOGGER.warning("SignalR error for %s, reconnecting in 15 s: %s", self.vehicle_id, err)
                await asyncio.sleep(15)

    async def _keyfob_sync_loop(self) -> None:
        """Periodically send CarCommand 21 to detect keyfob-triggered state changes."""
        while True:
            await asyncio.sleep(KEYFOB_SYNC_INTERVAL)
            try:
                await self.api.send_command(self.vehicle_id, CMD_REFRESH_RS)
                _LOGGER.debug("Keyfob sync sent for vehicle %s", self.vehicle_id)
            except asyncio.CancelledError:
                return
            except Exception as err:
                _LOGGER.debug("Keyfob sync failed: %s", err)
