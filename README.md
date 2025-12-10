# Teltonika FOTA for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Monitor and manage your Teltonika GPS/telematics devices through [FOTA WEB](https://fota.teltonika.lt).

> **Disclaimer:** This is an unofficial community integration and is not affiliated with, endorsed by, or supported by Teltonika. Use at your own risk.

## Features

**Device Sensors:** Activity status, firmware version, model, last connection, task queue, pending tasks

**Account Sensors:** Total/online/offline devices, pending/failed tasks, groups count

**Binary Sensors:** Online status, firmware update pending

**Services:** Refresh devices, cancel tasks

## Installation

### HACS (Recommended)
1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/manjotsc/ha-fota-teltonika` as Integration
3. Search "Teltonika FOTA" and install
4. Restart Home Assistant

### Manual
Copy `custom_components/teltonika_fota` to your `config/custom_components/` directory.

## Setup

1. Get your API token from [FOTA WEB](https://fota.teltonika.lt) → Settings → API Tokens → Add "API integration token"
2. In Home Assistant: Settings → Devices & Services → Add Integration → "Teltonika FOTA"
3. Enter your API token

## Options

- **Update interval:** 1-60 minutes
- **Enabled sensors:** Choose which sensors to create
- **Monitored devices:** Select specific devices

## Links

- [Report Issues](https://github.com/manjotsc/ha-fota-teltonika/issues)
- [FOTA WEB Documentation](https://wiki.teltonika-gps.com/view/FOTA_WEB)

## License

[MIT](LICENSE)
