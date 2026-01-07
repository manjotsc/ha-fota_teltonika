<p align="center">
  <img src="custom_components/fota_teltonika/icons/logo.png" alt="Teltonika FOTA" width="128" height="128">
</p>

<h1 align="center">Teltonika FOTA for Home Assistant</h1>

<p align="center">
  Monitor and manage your Teltonika GPS/telematics devices through <a href="https://fota.teltonika.lt">FOTA WEB</a>
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS Custom"></a>
  <a href="https://github.com/manjotsc/ha-fota_teltonika/releases"><img src="https://img.shields.io/github/v/release/manjotsc/ha-fota-teltonika?style=for-the-badge" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/manjotsc/ha-fota-teltonika?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/manjotsc/ha-fota_teltonika/stargazers"><img src="https://img.shields.io/github/stars/manjotsc/ha-fota-teltonika?style=for-the-badge" alt="Stars"></a>
  <a href="https://github.com/manjotsc/ha-fota_teltonika/issues"><img src="https://img.shields.io/github/issues/manjotsc/ha-fota-teltonika?style=for-the-badge" alt="Issues"></a>
</p>

---

> **Disclaimer:** This is an unofficial community integration and is not affiliated with, endorsed by, or supported by Teltonika. Use at your own risk.

## Overview

This integration connects your Home Assistant instance to the Teltonika FOTA WEB platform, enabling you to monitor device status, track firmware updates, and manage device tasks directly from your smart home dashboard.

## Features

### Device Monitoring
| Sensor | Description |
|--------|-------------|
| Activity Status | Current device activity state |
| Firmware Version | Installed firmware version |
| Model | Device model identifier |
| Last Connection | Timestamp of last device connection |
| Task Queue | Number of tasks in queue |
| Pending Tasks | Tasks awaiting execution |

### Account Overview
| Sensor | Description |
|--------|-------------|
| Total Devices | Total number of registered devices |
| Online Devices | Devices currently online |
| Offline Devices | Devices currently offline |
| Pending Tasks | Total pending tasks across all devices |
| Failed Tasks | Total failed tasks |
| Groups Count | Number of device groups |

### Binary Sensors
- **Online Status** — Real-time device connectivity
- **Firmware Update Pending** — Indicates available firmware updates

### Controls
- **Refresh Data** — Force refresh all data from the API
- **Cancel Pending Tasks** — Cancel all pending tasks for a device

### Services
| Service | Description |
|---------|-------------|
| `fota_teltonika.refresh_devices` | Manually refresh device data |
| `fota_teltonika.cancel_task` | Cancel a specific pending task |

## Prerequisites

- Home Assistant 2024.1.0 or newer
- A Teltonika FOTA WEB account with API access
- At least one Teltonika device registered in FOTA WEB

## Installation

### HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations** → click the **⋮** menu → **Custom repositories**
3. Add the repository URL:
   ```
   https://github.com/manjotsc/ha-fota_teltonika
   ```
4. Select **Integration** as the category
5. Click **Add**
6. Search for **"Teltonika FOTA"** and click **Download**
7. **Restart Home Assistant**

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/manjotsc/ha-fota_teltonika/releases)
2. Extract and copy the `fota_teltonika` folder to:
   ```
   <config>/custom_components/fota_teltonika
   ```
3. Restart Home Assistant

## Configuration

### Obtaining an API Token

1. Log in to [FOTA WEB](https://fota.teltonika.lt)
2. Navigate to **Settings** → **API Tokens**
3. Click **Add** and select **"API integration token"**
4. Copy the generated token

### Adding the Integration

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **"Teltonika FOTA"**
4. Enter your API token when prompted

### Options

| Option | Range | Description |
|--------|-------|-------------|
| Update Interval | 1–60 minutes | How often to poll the FOTA API |
| Enabled Sensors | Checkboxes | Select which sensors to create |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Integration not appearing | Ensure files are in the correct directory and restart HA |
| Authentication failed | Verify your API token is valid and has not expired |
| Devices not updating | Check your update interval and API rate limits |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Resources

- [Report Issues](https://github.com/manjotsc/ha-fota_teltonika/issues)
- [FOTA WEB Documentation](https://wiki.teltonika-gps.com/view/FOTA_WEB)
- [Teltonika GPS Wiki](https://wiki.teltonika-gps.com/)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
