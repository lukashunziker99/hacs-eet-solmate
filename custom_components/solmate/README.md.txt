# EET SolMate Home Assistant Integration

Native Home Assistant integration for EET SolMate via WebSocket.

## Features
- PV Power sensor
- Battery SOC
- Grid power
- Consumption
- Auto reconnect
- Native HA integration (no MQTT)

## Installation (HACS)

1. Add this repo to HACS as custom integration
2. Install "EET SolMate"
3. Restart Home Assistant
4. Add integration via UI

## Configuration

- Host: IP of SolMate
- Port: WebSocket port

## Notes

Replaces external MQTT bridge approach.