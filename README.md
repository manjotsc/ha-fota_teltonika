# Teltonika FOTA Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for [Teltonika FOTA WEB](https://fota.teltonika.lt) - manage and monitor your Teltonika GPS/telematics devices.

## Features

### Sensors (Per Device)
- **Activity Status** - Online/Offline/Inactive status
- **Firmware Version** - Current firmware version
- **Task Queue** - Number of pending tasks
- **Model** - Device model
- **Last Connection** - Last connection timestamp

### Sensors (Account Level)
- **Total Devices** - Total device count
- **Online Devices** - Devices connected in last 24h
- **Offline Devices** - Devices not seen in 24h
- **Pending Tasks** - Tasks waiting to execute
- **Failed Tasks** - Failed task count
- **Groups** - Device group count
- **Total Tasks** - Total task count

### Binary Sensors (Per Device)
- **Online** - Connectivity status
- **Has Pending Tasks** - Any queued tasks
- **Firmware Update Pending** - Firmware task in queue

### Services
| Service | Description |
|---------|-------------|
| `teltonika_fota.refresh_devices` | Force refresh all device data |
| `teltonika_fota.create_firmware_task` | Schedule firmware update |
| `teltonika_fota.create_config_task` | Schedule configuration update |
| `teltonika_fota.cancel_task` | Cancel a specific task |
| `teltonika_fota.bulk_cancel_tasks` | Cancel multiple tasks |
| `teltonika_fota.retry_failed_tasks` | Retry failed tasks in batch |

## Installation

### HACS (Recommended)
1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/manjotsc/ha-fota-teltonika`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Teltonika FOTA" and install

### Manual Installation
1. Download the `custom_components/teltonika_fota` folder
2. Copy it to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Teltonika FOTA"
4. Enter your API token from [FOTA WEB](https://fota.teltonika.lt)
   - Log in to FOTA WEB
   - Go to Settings → API Tokens
   - Create an "API integration token"
5. Click Submit

### Options
After setup, you can configure:
- **Update interval** - How often to fetch data (1-60 minutes)
- **Monitored devices** - Select specific devices to monitor

## API Token

To create an API token:
1. Log in to [FOTA WEB](https://fota.teltonika.lt)
2. Go to the top right corner → Settings → API Tokens
3. Click "Add Token"
4. Select "API integration token"
5. Copy the generated token (you won't be able to see it again)

## Example Automations

### Alert when device goes offline
```yaml
automation:
  - alias: "Teltonika Device Offline Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.teltonika_fmb920_123456789012345_online
        to: "off"
        for:
          hours: 1
    action:
      - service: notify.mobile_app
        data:
          title: "Device Offline"
          message: "Teltonika device has been offline for 1 hour"
```

### Notify on failed firmware update
```yaml
automation:
  - alias: "Firmware Update Failed"
    trigger:
      - platform: numeric_state
        entity_id: sensor.teltonika_fota_account_failed_tasks
        above: 0
    action:
      - service: notify.mobile_app
        data:
          title: "FOTA Alert"
          message: "There are failed firmware update tasks"
```

## Troubleshooting

### Cannot connect
- Verify your API token is correct
- Check your network connection
- Ensure the token has not expired

### Devices not showing
- Wait for the initial data fetch (up to 5 minutes)
- Check the Home Assistant logs for errors
- Verify devices are visible in FOTA WEB

## Support

- [Report Issues](https://github.com/manjotsc/ha-fota-teltonika/issues)
- [Teltonika FOTA Documentation](https://wiki.teltonika-gps.com/view/FOTA_WEB)

## License

MIT License - see [LICENSE](LICENSE) for details.
