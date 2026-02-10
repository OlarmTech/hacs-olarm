# Olarm Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integration for [Olarm](https://www.olarm.com/) smart alarm communicators. Olarm transforms traditional alarm systems into connected, app-controlled security solutions, working with major alarm panels (Paradox, DSC, Texecom, IDS, Honeywell and more).

## Supported Devices

- Olarm GEN1 – Paradox
- Olarm GEN1 – Universal
- Olarm PRO
- Olarm PRO 4G
- Olarm MAX
- Olarm HUB - coming Q2 2026

## Features

- Real-time monitoring via MQTT
- Binary sensors for alarm zones, areas, and system status
- LINK module support for expanded I/O capabilities
- MAX module support
- Olarm HUB integration
- OAuth2 authentication

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

## Known Limitations

- Maximum of 5 Olarm devices per integration instance
- Only one Olarm user account per Home Assistant instance

## Issues / Feature Requests

Please log issues and feature requests in Github issues 👆

## Contributing

Contributions are welcome! Please open an issue or submit a pull request. Please see CONTRIBUTING.md 

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
