# Olarm Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integration for [Olarm](https://www.olarm.com/) smart alarm communicators. Olarm transforms traditional alarm systems into connected, app-controlled security solutions, working with major alarm panels — Paradox, DSC, IDS, Texecom, Honeywell Galaxy and Orisec. See [Supported alarm panels](#supported-alarm-panels) for the model list.

Your areas become alarm control panels you can arm and disarm. Zones, power and I/O become binary sensors. PGMs, utility keys, LINK outputs and MAX outputs become buttons. Everything updates over MQTT, so state changes arrive as they happen rather than on a poll.

## Supported Devices

- Olarm GEN1 – Paradox
- Olarm GEN1 – Universal
- Olarm PRO
- Olarm PRO 4G
- Olarm MAX
- Olarm HUB - coming Q2 2026

## Supported alarm panels

Panels supported by **Olarm MAX**. Connect the panel to an Olarm MAX, enable API Access, and its areas, zones and outputs appear in Home Assistant through this integration.

| Brand | Panel | Adapter board | Notes |
|---|---|---|---|
| Paradox | Paradox MG5050 | — |  |
| Paradox | Paradox MG5050+ | — |  |
| Paradox | Paradox SP6000 | — |  |
| Paradox | Paradox SP6000+ | — |  |
| Paradox | Paradox SP65 | — |  |
| Paradox | Paradox EVO192 | Required |  |
| DSC | DSC PowerSeries PC1555 | — |  |
| DSC | DSC PowerSeries PC1616 | — |  |
| DSC | DSC PowerSeries PC832 | — |  |
| DSC | DSC PowerSeries PC864 | — |  |
| DSC | DSC PowerSeries PC1808 | — |  |
| DSC | DSC PowerSeries PC1832 | — |  |
| DSC | DSC PowerSeries PC1864 | — |  |
| DSC | DSC PowerSeries PC5005 | — |  |
| DSC | DSC PowerSeries PC5010 | — |  |
| DSC | DSC PowerSeries PC5015 | — |  |
| DSC | DSC PowerSeries PC5020 | — |  |
| DSC | DSC PowerSeries NEO HS2016 | Required |  |
| DSC | DSC PowerSeries NEO HS2032 | Required |  |
| DSC | DSC PowerSeries NEO HS2064 | Required |  |
| DSC | DSC PowerSeries NEO HS2128 | Required |  |
| IDS | IDS 805 | — |  |
| IDS | IDS 806 | Required |  |
| IDS | IDS X16 | Required |  |
| IDS | IDS X64 | Required |  |
| IDS | IDS X64 Serial | Required |  |
| Texecom | Texecom Premier 412 | — |  |
| Texecom | Texecom Premier 816 | — |  |
| Texecom | Texecom Premier 816 Plus | — |  |
| Texecom | Texecom Premier 832 | — |  |
| Texecom | Texecom Premier 168 | — | Limited app functionality |
| Texecom | Texecom Premier Elite 24 | — |  |
| Texecom | Texecom Premier Elite 48 | — |  |
| Texecom | Texecom Premier Elite 64 | — |  |
| Texecom | Texecom Premier Elite 64-W | — |  |
| Texecom | Texecom Premier Elite 64-W LIVE | — |  |
| Texecom | Texecom Premier Elite 88 | — |  |
| Texecom | Texecom Premier Elite 168 | — |  |
| Honeywell Galaxy | Honeywell Galaxy G2-12 | — |  |
| Honeywell Galaxy | Honeywell Galaxy G2-20 | — |  |
| Honeywell Galaxy | Honeywell Galaxy G2-44 | — |  |
| Honeywell Galaxy | Honeywell Galaxy G2-44+ | — |  |
| Honeywell Galaxy | Honeywell Galaxy G3 | — | G3 series |
| Honeywell Galaxy | Honeywell Galaxy Dimension GD48 | — |  |
| Honeywell Galaxy | Honeywell Galaxy Dimension GD96 | — |  |
| Honeywell Galaxy | Honeywell Galaxy Dimension GD264 | — |  |
| Honeywell Galaxy | Honeywell Galaxy Dimension GD520 | — |  |
| Orisec | Orisec CP-50 | Required |  |
| Orisec | Orisec CP-60 | Required |  |
| Orisec | Orisec CP-100 | Required |  |
| Orisec | Orisec ZP-10 | Required |  |
| Orisec | Orisec ZP-20 | Required |  |
| Orisec | Orisec ZP-40 | Required |  |
| Orisec | Orisec ZP-100 | Required |  |

Adapter boards are sold separately. Wiring and programming for each panel is on the [Olarm MAX install guides](https://www.olarm.com/install-guides/olarm-max). Which entities appear depends on what your panel reports — see [Entities](#entities).

## Features

- Alarm control panel per area — arm away, arm home (stay), arm night (sleep), disarm
- Binary sensors for zones, zone bypass, AC power, LINK and MAX I/O, and electric fence
- Buttons for PGM outputs, utility keys, zone bypass, LINK outputs and relays, MAX outputs, panic, and partial/custom arm profiles
- Real-time monitoring via MQTT
- LINK module support for expanded I/O capabilities
- MAX module support
- OAuth2 authentication

## Entities

What appears after setup depends on what your panel reports and which modules are attached. Nothing is created for hardware the device does not have.

### Alarm control panel

One per area, up to 8 areas / partitions.

| Supported feature | Olarm action |
|---|---|
| Arm away | `area-arm` |
| Arm home | `area-stay` |
| Arm night | `area-sleep` |
| Disarm | always available |

Arming options are built from the actions your panel actually reports, so a panel without a sleep mode will not show arm night. No code is required to arm or disarm.

Panel states map to Home Assistant as:

| Home Assistant state | Olarm area state |
|---|---|
| `disarmed` | `disarm`, `notready` |
| `armed_home` | `stay`, `stayarm1`–`stayarm4` |
| `armed_away` | `arm` |
| `armed_night` | `sleep` |
| `armed_custom_bypass` | `partarm1`–`partarm4`, `customarm1`–`customarm4` |
| `pending` | `entrydelay`, `countdown` |
| `triggered` | `alarm`, `emergency`, `fire`, `medical` |

Extra state attributes:

- `armed_custom_bypass_profile` — which partial or custom profile is active, when the state is `armed_custom_bypass`
- `zone_in_alarm` — the zone that triggered the area
- `zone_in_alarm_time` — when it triggered

### Binary sensors

| Sensor | On when |
|---|---|
| Zone | Zone is active |
| Zone Bypass | Zone is bypassed |
| AC Power | Panel mains power is OK |
| AC Power (fence) | Fence energizer mains power is OK |
| Input *(LINK)* | Input is high |
| Output *(LINK)* | Output is closed |
| Relay *(LINK)* | Relay is latched |
| MAX Input | Input is high |
| MAX Output | Output is closed |
| Fence Zone Energized | Fence zone is energized |
| Fence Zone Alarm | Fence zone is in alarm |
| Fence Zone Voltage Bad | Fence zone voltage is out of range |
| Fence Gate Alarm Or Open | Fence gate is in alarm or open |

Zones are given a device class from the zone type configured on your panel — door, window or motion — so they get the right icon and behaviour in the UI. Zones of other types have no device class.

### Buttons

| Button | What it does |
|---|---|
| Zone Bypass / Unbypass | Bypass or unbypass a zone |
| PGM Open / Close / Pulse | Drive a PGM output |
| Utility Key | Trigger a utility key mapped on the panel |
| User Panic | Raise a panic signal |
| Area Partial Arm 1–4 | Arm a partial-arm profile |
| Area Custom Arm 1–4 | Arm a custom-arm profile |
| Output Open / Close / Pulse *(LINK)* | Drive a LINK output |
| Relay Latch / Unlatch / Pulse *(LINK)* | Drive a LINK relay |
| MAX Output Open / Close / Pulse | Drive a MAX output |

Partial and custom arm profiles are buttons rather than alarm-panel modes because a single alarm control panel entity supports only one custom bypass action, while a panel may have up to four of each.

### Entity naming

Entity IDs are built from your device name plus the entity name, so they differ per install. A device named `Home` with an area labelled `House` gives:

```
alarm_control_panel.home_area_01_house
binary_sensor.home_zone_001_front_door
button.home_pgm_01_pulse_gate
```

Find yours under **Settings → Devices & Services → Olarm → entities**, or in **Developer Tools → States**. The examples below use placeholders — replace them with your own.

## Prerequisites

- An active Olarm account
- A compatible Olarm device connected to a supported alarm panel
- An active subscription for the device
- **API Access enabled** in the Olarm app
  - This needs to be enabled on the **primary user** if a secondary user is used for the integration.

### Important: Enable API Access

Before installing the integration:

1. Open the Olarm App of the **primary user**
2. Go to **Profile** > **Device List** > **[Select Device]** > **Developer Settings**
3. Enable **API Access**

## Installation via HACS

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. In Home Assistant, go to HACS > Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/olarmtech/hacs-olarm`
5. Select category: "Integration"
6. Click "Add"
7. Find "Olarm" in the integration list and click "Download"
8. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "+ Add Integration"
3. Search for "Olarm"
4. Follow the OAuth2 authentication flow
5. Select the device you want to add

Each config entry covers one Olarm device. To add another, repeat the steps and select the next device.

## How data updates

The integration fetches device state once when it loads, then subscribes to the Olarm MQTT brokers. There is no polling interval — updates are pushed as the panel reports them.

When you send a command, the entity moves to a pending state straight away for UI feedback and settles once the panel confirms over MQTT.

## Automation examples

Replace the entity IDs with your own — see [Entity naming](#entity-naming).

### Arm when everyone leaves

```yaml
automation:
  - alias: "Arm when everyone leaves"
    triggers:
      - trigger: state
        entity_id: group.family
        to: "not_home"
        for: "00:05:00"
    conditions:
      - condition: state
        entity_id: alarm_control_panel.home_area_01_house
        state: "disarmed"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          message: "Everyone's out. Arming in 60 seconds."
      - delay: "00:01:00"
      - action: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.home_area_01_house
```

### Flash lights and notify when the alarm triggers

```yaml
automation:
  - alias: "Alarm triggered"
    triggers:
      - trigger: state
        entity_id: alarm_control_panel.home_area_01_house
        to: "triggered"
    actions:
      - action: light.turn_on
        target:
          entity_id: light.lounge
        data:
          color_name: red
          flash: long
      - action: notify.mobile_app_your_phone
        data:
          title: "Alarm triggered"
          message: >-
            Zone: {{ state_attr('alarm_control_panel.home_area_01_house',
            'zone_in_alarm') }}
```

### Warn if a zone is open when arming

```yaml
automation:
  - alias: "Garage open at arming"
    triggers:
      - trigger: state
        entity_id: alarm_control_panel.home_area_01_house
        to: "armed_away"
    conditions:
      - condition: state
        entity_id: binary_sensor.home_zone_004_garage
        state: "on"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          message: "Armed with the garage zone still open."
```

### Open the gate with a PGM

```yaml
script:
  open_gate:
    alias: "Open gate"
    sequence:
      - action: button.press
        target:
          entity_id: button.home_pgm_01_pulse_gate
```

### Notify on mains power loss

```yaml
automation:
  - alias: "Mains power lost"
    triggers:
      - trigger: state
        entity_id: binary_sensor.home_ac_power
        to: "off"
        for: "00:02:00"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          message: "Alarm panel has lost mains power."
```

### Alert on fence voltage

```yaml
automation:
  - alias: "Fence voltage bad"
    triggers:
      - trigger: state
        entity_id: binary_sensor.home_fence_zone_01_voltage_bad
        to: "on"
    actions:
      - action: notify.mobile_app_your_phone
        data:
          message: "Electric fence voltage is out of range."
```

## Known Limitations

- Maximum of 5 Olarm devices per integration instance
- Only one Olarm user account per Home Assistant instance
- No custom actions (services) are provided — use the standard `alarm_control_panel` and `button` actions shown above
- Arming options are limited to what your panel reports. A panel that does not support sleep mode will not offer arm night.

## Troubleshooting

**"No devices found" during setup.** API Access is not enabled, or it was enabled on a secondary user. It must be enabled on the **primary user** of the device — see [Enable API Access](#important-enable-api-access).

**Setup fails with a rate limit error.** The Olarm API is rate limited. Wait a few minutes and try again.

**Entities show as unavailable or state looks stale.** Check that the device is online in the Olarm app first. If it is, reload the integration under **Settings → Devices & Services → Olarm → Reload**.

**An area does not offer arm night or arm home.** The integration only exposes the arming modes your panel reports. Confirm the mode exists on the panel and in the Olarm app.

**No PGM, utility key or LINK entities.** These are only created when the device reports them. Confirm they are configured on the panel and visible in the Olarm app.

**Commands do nothing.** A command is sent to the Olarm cloud and applied by the panel. If the panel rejects it — for example arming an area that is not ready — the entity returns to its previous state. Check the Olarm app event log.

To gather logs for an issue, add this to `configuration.yaml` and restart:

```yaml
logger:
  default: warning
  logs:
    custom_components.olarm: debug
```

## Issues / Feature Requests

Please log issues and feature requests in Github issues 👆

## Contributing

Contributions are welcome! Please open an issue or submit a pull request. Please see CONTRIBUTING.md 

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
