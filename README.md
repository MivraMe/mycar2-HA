# MyCar2 — Home Assistant Integration

Home Assistant integration for the **MyCar2** OBD-II tracker (Automobility).  
Monitor and control your vehicle in real time from Home Assistant.

---

## Features

- **Real-time updates** via SignalR (SSE) — state changes appear instantly
- **REST polling** every 30 seconds as a fallback
- **Automatic keyfob sync** every 5 minutes
- **Remote start / stop**, door lock, trunk release, panic, valet mode
- **GPS tracking** with altitude, heading, and speed
- **Battery voltage**, interior temperature, signal strength
- **Multi-vehicle** — one config entry per vehicle

---

## Installation via HACS

1. In HACS, open **Integrations** → ⋮ menu → **Custom repositories**
2. Add the repository URL and select the **Integration** category
3. Search for **MyCar2** and click **Download**
4. Restart Home Assistant

### Manual installation

Copy the `custom_components/mycar2/` folder into your `config/custom_components/` directory, then restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **MyCar2**
3. Enter your MyCar2 **email** and **password**
4. If you have multiple vehicles, select the one to connect
5. The device and all its entities appear immediately

> Credentials are stored encrypted by Home Assistant. Never put them in a YAML file.

---

## Entities

### Lock

| Entity | Description |
|---|---|
| `lock.{name}_doors` | Lock / unlock the doors |

**Available actions:** `lock.lock`, `lock.unlock`

```yaml
# Example — lock when leaving home
automation:
  trigger:
    - platform: state
      entity_id: person.you
      to: not_home
  action:
    - action: lock.lock
      target:
        entity_id: lock.my_car_doors
```

---

### Binary Sensors

| Entity | Device class | Description |
|---|---|---|
| `binary_sensor.{name}_engine` | `running` | Engine running (remote start active) |
| `binary_sensor.{name}_ignition` | `power` | Ignition on |
| `binary_sensor.{name}_trunk` | `opening` | Trunk open |
| `binary_sensor.{name}_hood` | `opening` | Hood open |
| `binary_sensor.{name}_doors` | `door` | At least one door open |
| `binary_sensor.{name}_offline` | `connectivity` | Device offline |

---

### Sensors

| Entity | Unit | Description |
|---|---|---|
| `sensor.{name}_battery` | V | Vehicle battery voltage |
| `sensor.{name}_gps_speed` | km/h | Instantaneous GPS speed |
| `sensor.{name}_signal` | dBm | Cellular signal strength (RSSI) |
| `sensor.{name}_interior_temperature` | °C | Interior temperature |
| `sensor.{name}_firmware_version` | — | Module firmware version *(disabled by default)* |

---

### Buttons

| Entity | CarCommand | Description |
|---|---|---|
| `button.{name}_remote_start` | 3 | Remote start |
| `button.{name}_remote_stop` | 4 | Remote stop |
| `button.{name}_extend_runtime` | 5 | Extend remote start duration |
| `button.{name}_trunk_release` | 2 | Release the trunk |
| `button.{name}_panic_on` | 6 | Activate panic alarm |
| `button.{name}_panic_off` | 7 | Deactivate panic alarm |
| `button.{name}_valet_mode` | 20 | Toggle valet mode |
| `button.{name}_sync_status` | 21 | Force a status refresh *(disabled by default)* |

> **Remote Start**, **Remote Stop**, and **Trunk Release** automatically send a wake command (`CarCommand 9`) before executing if the device is offline.

```yaml
# Example — start the car 30 minutes before leaving in the morning
automation:
  trigger:
    - platform: time
      at: "07:30:00"
  condition:
    - condition: state
      entity_id: binary_sensor.my_car_engine
      state: "off"
  action:
    - action: button.press
      target:
        entity_id: button.my_car_remote_start
```

---

### Device Tracker

| Entity | Description |
|---|---|
| `device_tracker.{name}_location` | Vehicle GPS position |

Returns `home` / `not_home` or the name of a **HA zone** if the vehicle is within one.

**Extra attributes:**

| Attribute | Description |
|---|---|
| `altitude` | Altitude in metres |
| `heading` | Bearing in degrees (0–360) |
| `speed` | Speed in km/h |

```yaml
# Example — notify when the car arrives home
automation:
  trigger:
    - platform: state
      entity_id: device_tracker.my_car_location
      to: home
  action:
    - action: notify.mobile_app
      data:
        message: "The car has arrived home!"
```

---

## Exposing Entities

### Google Assistant / Alexa

1. Go to **Settings → Devices & Services → Google Assistant** (or Alexa)
2. Select the entities you want to expose
3. The lock (`lock`) and tracker (`device_tracker`) are the most useful

> For security, **do not expose** remote start buttons to voice assistants without a PIN code confirmation.

### Lovelace Dashboard

A ready-to-paste control card:

```yaml
type: vertical-stack
cards:
  - type: entity
    entity: lock.my_car_doors
    name: Door Lock

  - type: glance
    entities:
      - entity: binary_sensor.my_car_engine
        name: Engine
      - entity: binary_sensor.my_car_ignition
        name: Ignition
      - entity: binary_sensor.my_car_trunk
        name: Trunk
      - entity: binary_sensor.my_car_hood
        name: Hood
      - entity: sensor.my_car_battery
        name: Battery
      - entity: sensor.my_car_signal
        name: Signal

  - type: map
    entities:
      - entity: device_tracker.my_car_location
    hours_to_show: 1

  - type: horizontal-stack
    cards:
      - type: button
        entity: button.my_car_remote_start
        name: Start
        icon: mdi:car-key
      - type: button
        entity: button.my_car_remote_stop
        name: Stop
        icon: mdi:car-off
      - type: button
        entity: button.my_car_trunk_release
        name: Trunk
        icon: mdi:car-back
```

---

## How It Works

| Mechanism | Detail |
|---|---|
| **Authentication** | AWS Cognito `USER_PASSWORD_AUTH` — token refreshed automatically every 55 min |
| **Real-time** | SignalR over SSE — automatic reconnection with 15 s back-off |
| **Fallback** | REST polling `GetLastVehicleStatus` + `GetLastVehiclePosition` every 30 s |
| **Keyfob sync** | `CarCommand 21` sent every 5 min to detect local state changes |
| **Wake on command** | `CarCommand 9` sent automatically before any action when `IsOffline = true` |

---

## Troubleshooting

**Integration fails to connect**  
→ Check your email and password in the official MyCar2 app first.

**Entities are not updating**  
→ The device may be offline (`binary_sensor.{name}_offline = on`). Press **Sync Status** to wake it.

**GPS position is missing or stale**  
→ Expected in underground parking. Position resumes once GPS signal is restored.

**Error after a HA update**  
→ Delete the integration, restart HA, and re-add it.

---

## Requirements

| Software | Minimum version |
|---|---|
| Home Assistant | 2024.1.0 |
| HACS | 1.34.0 |

---

## License

MIT
