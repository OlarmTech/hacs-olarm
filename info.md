# Olarm Integration

Connect your Olarm smart alarm communicator to Home Assistant for real-time monitoring and automation.

## What is Olarm?

[Olarm](https://www.olarm.com) transforms traditional alarm systems into connected, app-controlled security solutions. Works with major alarm panels including Paradox MG5050 and EVO192, DSC PowerSeries and PowerSeries NEO, IDS 805, 806 and X-Series, Texecom Premier and Premier Elite, Honeywell Galaxy G2, G3 and Dimension, and Orisec CP and ZP. Full model list is in the README.

## Features

- **Alarm Control Panels**: One per area — arm away, home and night, and disarm
- **Binary Sensors**: Zones, zone bypass, AC power, LINK/MAX I/O and electric fence
- **Buttons**: PGM outputs, utility keys, zone bypass, LINK and MAX outputs, panic, partial and custom arm profiles
- **Real-time Updates**: MQTT-based push notifications for instant status changes
- **OAuth2 Authentication**: Secure cloud connection
- **Easy Setup**: Configure through Home Assistant UI

## Supported Devices

- Olarm GEN1 (Paradox & Universal)
- Olarm PRO / PRO 4G
- Olarm MAX

## Prerequisites

- Active Olarm account with subscription
- Compatible Olarm device connected to your alarm panel
- **API Access enabled** in the Olarm app (Profile > Device List > [Device] > Developer Settings > Enable)

## Getting Started

1. Enable API Access in the Olarm app
2. Install this integration via HACS
3. Go to Settings > Devices & Services
4. Click "+ Add Integration" and search for "Olarm"
5. Complete OAuth2 authentication
6. Select the device you want to add — each config entry covers one Olarm device

For more information, visit [Olarm Website](https://www.olarm.com)
