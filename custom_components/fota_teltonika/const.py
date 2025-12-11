"""Constants for the Teltonika FOTA integration."""
from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

# Domain
DOMAIN: Final = "fota_teltonika"

# API Configuration
BASE_URL: Final = "https://api.teltonika.lt"
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=5)
MIN_SCAN_INTERVAL_MINUTES: Final = 1
MAX_SCAN_INTERVAL_MINUTES: Final = 60

# Config entry keys
CONF_API_TOKEN: Final = "api_token"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_MONITORED_DEVICES: Final = "monitored_devices"
CONF_ENABLED_SENSORS: Final = "enabled_sensors"

# Available sensor keys for selection
SENSOR_KEYS: Final[dict[str, str]] = {
    "activity_status": "Activity Status",
    "firmware_version": "Firmware Version",
    "task_queue_count": "Task Queue Count",
    "model": "Model",
    "last_connection": "Last Connection",
    "online": "Online (Binary)",
    "has_pending_tasks": "Has Pending Tasks",
    "firmware_update_pending": "Firmware Update Pending (Binary)",
}

# API Endpoints
ENDPOINT_DEVICES: Final = "/devices"
ENDPOINT_TASKS: Final = "/tasks"
ENDPOINT_TASKS_BULK_CANCEL: Final = "/tasks/bulkCancel"
ENDPOINT_BATCHES: Final = "/batches"
ENDPOINT_COMPANY_STATS: Final = "/companies/stats"

# Device Properties
ATTR_IMEI: Final = "imei"
ATTR_MODEL: Final = "model"
ATTR_FIRMWARE_VERSION: Final = "firmware_version"
ATTR_ACTIVITY_STATUS: Final = "activity_status"
ATTR_TASK_QUEUE: Final = "task_queue"
ATTR_LAST_CONNECTION: Final = "last_connection"
ATTR_SERIAL: Final = "serial"

# Activity Status Values (API returns capitalized values)
STATUS_ONLINE: Final = "Online"
STATUS_OFFLINE: Final = "Offline"
STATUS_INACTIVE: Final = "Inactive"

# Task Types
TASK_TYPE_FIRMWARE: Final = "firmware"
TASK_TYPE_CONFIGURATION: Final = "configuration"

# Task Statuses
TASK_STATUS_PENDING: Final = "pending"
TASK_STATUS_RUNNING: Final = "running"
TASK_STATUS_COMPLETED: Final = "completed"
TASK_STATUS_FAILED: Final = "failed"
TASK_STATUS_CANCELLED: Final = "cancelled"

# Service Names
SERVICE_REFRESH_DEVICES: Final = "refresh_devices"
SERVICE_CREATE_FIRMWARE_TASK: Final = "create_firmware_task"
SERVICE_CREATE_CONFIG_TASK: Final = "create_config_task"
SERVICE_CANCEL_TASK: Final = "cancel_task"
SERVICE_BULK_CANCEL_TASKS: Final = "bulk_cancel_tasks"
SERVICE_RETRY_FAILED_TASKS: Final = "retry_failed_tasks"

# Platforms
PLATFORMS: Final[list[Platform]] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]
