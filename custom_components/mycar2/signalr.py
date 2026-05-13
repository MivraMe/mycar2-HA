import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

_RECORD_SEP = "\x1e"
_KEEPALIVE_TYPE = 6


class SignalRClient:
    """Minimal SignalR-over-SSE client for VehicleStatusHub."""

    def __init__(self, base_url: str, vehicle_id: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._vehicle_id = vehicle_id

    async def stream(
        self, session: aiohttp.ClientSession, token: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Yield StatusUpdated payloads from the SignalR SSE stream."""
        hub_url = f"{self._base_url}/VehicleStatusHub"
        auth = {"Authorization": f"Bearer {token}"}

        # 1. Negotiate
        async with session.post(
            f"{hub_url}/negotiate?negotiateVersion=1",
            headers={**auth, "Content-Length": "0"},
        ) as resp:
            resp.raise_for_status()
            neg = await resp.json(content_type=None)

        conn_id = neg.get("connectionToken") or neg.get("connectionId")
        if not conn_id:
            raise ValueError(f"No connection token in negotiate response: {neg}")
        params = f"?id={conn_id}"
        post_headers = {**auth, "Content-Type": "text/plain;charset=UTF-8"}

        # 2. Protocol handshake
        handshake = json.dumps({"protocol": "json", "version": 1}) + _RECORD_SEP
        async with session.post(f"{hub_url}{params}", data=handshake, headers=post_headers) as resp:
            resp.raise_for_status()

        # 3. Join group for this vehicle
        join = (
            json.dumps({"type": 1, "target": "JoinGroup", "arguments": [self._vehicle_id]})
            + _RECORD_SEP
        )
        async with session.post(f"{hub_url}{params}", data=join, headers=post_headers) as resp:
            resp.raise_for_status()

        # 4. SSE stream
        _LOGGER.debug("SignalR SSE stream open for vehicle %s", self._vehicle_id)
        sse_headers = {**auth, "Accept": "text/event-stream"}
        buf = b""
        async with session.get(f"{hub_url}{params}", headers=sse_headers) as resp:
            resp.raise_for_status()
            async for chunk in resp.content.iter_chunked(4096):
                buf += chunk
                while b"\n" in buf:
                    raw_line, buf = buf.split(b"\n", 1)
                    line = raw_line.decode("utf-8", errors="replace").rstrip("\r")
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].lstrip(" ")
                    for part in data_str.split(_RECORD_SEP):
                        part = part.strip()
                        if not part:
                            continue
                        try:
                            msg = json.loads(part)
                        except json.JSONDecodeError:
                            _LOGGER.debug("Unparseable SSE fragment: %r", part)
                            continue
                        if msg.get("type") == _KEEPALIVE_TYPE:
                            continue
                        if msg.get("target") == "StatusUpdated" and msg.get("arguments"):
                            try:
                                yield json.loads(msg["arguments"][0])
                            except (json.JSONDecodeError, KeyError, IndexError) as err:
                                _LOGGER.debug("Failed to decode StatusUpdated payload: %s", err)
