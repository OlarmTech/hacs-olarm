# Olarm Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integration for [Olarm](https://www.olarm.com/) smart alarm communicators. Olarm connects traditional alarm panels — Paradox, DSC, Texecom, IDS, Honeywell Galaxy, Orisec and more — to Home Assistant, without replacing the panel on your wall.

Your areas become alarm control panel entities you can arm and disarm. Your zones become binary sensors you can automate against. PGMs, utility keys and I/O become buttons.

**Cloud push** — state arrives over MQTT in real time, so there is no polling interval to tune.

---

## Supported devices

| Device | Notes |
|---|---|
| Olarm GEN1 – Paradox | |
| Olarm GEN1 – Universal | |
| Olarm PRO | |
| Olarm PRO 4G | |
| Olarm MAX | Adds MAX I/O entities |
| Olarm HUB | Coming Q2 2026 |

LINK modules are supported on compatible devices and add their own input, output and relay entities.

---

## Entities

The integration creates entities from your device profile, so you only get what your panel actually reports. Names come from the labels you have already set in the Olarm app — a zone labelled "Front Door" arrives as `Zone 001 - Front Door`.

### Alarm control panel

One entity per area, up to 8 areas or partitions.

| Supported action | Home Assistant state |
|---|---|
| Arm | `armed_away` |
| Stay | `armed_home` |
| Sleep | `armed_night` |
| Disarm | `disarmed` |
| Partial arm 1–4, custom arm 1–4 | `armed_custom_bypass` |
| Entry delay, exit countdown | `pending` |
| Alarm, emergency, fire, medical | `triggered` |

No code is required to arm or disarm from Home Assistant.

Partial and custom arm profiles are exposed as **buttons** rather than panel actions, because a panel entity supports a single custom-bypass action while alarm systems may offer up to four partial-arming profiles per area.

### Binary sensors

| Entity | Device class | Example name |
|---|---|---|
| Zone | `door`, `window`, `motion` — mapped from the zone type | `Zone 001 - Front Door` |
| Zone bypass | — | `Zone 001 Bypass - Front Door` |
| AC power | `power` | Named after the device |
| AC power (fence) | `power` | Named after the fence |
| LINK input / output | — | `Input 01 - Gate` |
| LINK relay output | — | `Relay 01 - Garage` |
| MAX input / output | — | `MAX Output 01 - Gate` |
| Fence zone energized | — | `Fence Zone 01 Energized - North` |
| Fence zone alarm | — | `Fence Zone 01 Alarm - North` |
| Fence zone voltage bad | — | `Fence Zone 01 Voltage Bad - North` |
| Fence gate alarm open | — | Named after the gate |

Panels support up to **192 zones**.

### Buttons

| Button | Example name |
|---|---|
| Zone bypass / unbypass | `Zone 001 Bypass - Front Door` |
| PGM open / close / pulse | `PGM 01 Open - Gate` |
| Utility key | `Utility Key 01 - Garage` |
| Area partial arm 1–4 | `Area 01 Partial Arm 1 - House` |
| Area custom arm 1–4 | `Area 01 Custom Arm 1 - House` |
| LINK output open / close / pulse | `Gate LINK Output 01 Open - Driveway` |
| LINK relay unlatch | `Gate LINK Relay 01 Unlatch - Driveway` |
| MAX output open / close / pulse | `MAX Output 01 Pulse - Garage` |
| User panic | `User Panic` |

---

## Prerequisites

- An active Olarm account
- A compatible Olarm device connected to a supported alarm panel
- An active subscription for the device
- **API Access enabled** in the Olarm app

### Important: enable API Access first

The integration cannot see your device until this is done, and it must be done on the **primary user** account — even if you intend to connect Home Assistant with a secondary user.

1. Open the Olarm app, signed in as the **primary user**
2. Go to **Profile** → **Device List** → **[select your device]** → **Developer Settings**
3. Enable **API Access**

---

## Installation via HACS

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. In Home Assistant, go to **HACS** → **Integrations**
3. Click the three dots, top right, and choose **Custom repositories**
4. Add `https://github.com/olarmtech/hacs-olarm`
5. Category: **Integration**
6. Click **Add**
7. Find **Olarm** in the list and click **Download**
8. Restart Home Assistant

## Configuration

1. **Settings** → **Devices & Services**
2. **+ Add Integration**
3. Search for **Olarm**
4. Complete the OAuth2 sign-in

---

## Automation examples

Entity IDs are generated from your own labels, so adjust these to match what appears in **Developer Tools → States**.

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
        entity_id: alarm_control_panel.house
        state: "disarmed"
    actions:
      - action: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.house
```

### Flash the lights when the alarm triggers

```yaml
automation:
  - alias: "Alarm triggered - visual alert"
    triggers:
      - trigger: state
        entity_id: alarm_control_panel.house
        to: "triggered"
    actions:
      - action: light.turn_on
        target:
          entity_id: light.living_room
        data:
          color_name: red
          flash: long
      - action: notify.mobile_app
        data:
          title: "Alarm triggered"
          message: "The house alarm is going off."
```

### Warn when mains power fails

Useful anywhere loadshedding or outages are routine — the panel runs on battery backup, and this tells you the clock has started.

```yaml
automation:
  - alias: "Mains power lost"
    triggers:
      - trigger: state
        entity_id: binary_sensor.olarm_ac_power
        to: "off"
        for: "00:02:00"
    actions:
      - action: notify.mobile_app
        data:
          message: "Mains power is out. The alarm is running on battery."
```

### Open the gate from a dashboard button

```yaml
script:
  open_gate:
    alias: "Open gate"
    sequence:
      - action: button.press
        target:
          entity_id: button.pgm_01_pulse_gate
```

### Bypass a faulty zone before arming

```yaml
automation:
  - alias: "Bypass garage PIR at night"
    triggers:
      - trigger: time
        at: "22:30:00"
    actions:
      - action: button.press
        target:
          entity_id: button.zone_014_bypass_garage_pir
      - delay: "00:00:05"
      - action: alarm_control_panel.alarm_arm_night
        target:
          entity_id: alarm_control_panel.house
```

---

## Known limitations

- Maximum of **5 Olarm devices** per integration instance
- Only **one Olarm user account** per Home Assistant instance
- Arming a partial or custom profile uses a button, not the alarm panel entity
- Quality scale is **bronze**

---

## Troubleshooting

**The integration finds no devices.**
API Access is almost certainly not enabled, or it was enabled on a secondary account. It must be enabled on the **primary user** — see Prerequisites above.

**Entities are missing for zones I can see in the app.**
Entities are built from the device profile. If you have relabelled or added zones recently, reload the integration from **Settings → Devices & Services → Olarm → Reload**.

**States are not updating.**
The integration uses MQTT push rather than polling. Check that the device shows as online in the Olarm app first — if it is offline there, Home Assistant has nothing to receive.

**Zone shows as the wrong device class.**
Device class is mapped from the zone type set on the panel, not in Home Assistant. Door, window and motion types are mapped; other types fall back to a generic sensor.

---

## Issues and feature requests

Please log issues and feature requests in [GitHub issues](https://github.com/olarmtech/hacs-olarm/issues).

## Contributing

Contributions are welcome. Please open an issue or submit a pull request — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
