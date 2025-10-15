# Olarm Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

This is a custom integration for [Olarm](https://www.olarm.com/) alarm systems for Home Assistant, available through HACS while awaiting official Home Assistant core approval.

## Features

- OAuth2 authentication with Olarm
- Real-time monitoring via MQTT
- Binary sensors for alarm zones and system status
- Configuration through Home Assistant UI

## Installation

### HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. In Home Assistant, go to HACS > Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/olarmtech/hacs-olarm` (or your actual GitHub URL)
5. Select category: "Integration"
6. Click "Add"
7. Find "Olarm" in the integration list and click "Download"
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/olarm` folder to your Home Assistant's `custom_components` directory
2. If the `custom_components` directory doesn't exist, create it in the same location as your `configuration.yaml`
3. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "+ Add Integration"
3. Search for "Olarm"
4. Follow the OAuth2 authentication flow to link your Olarm account

## Requirements

- Home Assistant 2024.1.0 or newer
- Olarm account with active alarm system
- Internet connection for OAuth2 and MQTT

## Dependencies

This integration requires:
- `olarmflowclient==1.0.2` (automatically installed)
- Home Assistant Application Credentials component

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/olarmtech/hacs-olarm).

For Olarm-specific support, visit [Olarm Support](https://www.olarm.com/support).

## License

This integration is released under the Apache License 2.0. See [LICENSE](LICENSE) for details.
