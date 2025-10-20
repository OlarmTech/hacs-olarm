# Olarm Integration

Connect your Olarm smart alarm communicator to Home Assistant for real-time monitoring and automation.

## What is Olarm?

[Olarm](https://www.olarm.com) transforms traditional alarm systems into connected, app-controlled security solutions. Works with major alarm panels including Paradox, DSC, Texecom, IDS, and Honeywell.

## Features

- **Real-time Updates**: MQTT-based push notifications for instant status changes
- **Binary Sensors**: Monitor zones, system status, and LINK/MAX modules
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
6. Your devices will be automatically discovered

For more information, visit [Olarm Website](https://www.olarm.com)
