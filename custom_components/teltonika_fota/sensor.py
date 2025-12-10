"""Sensor platform for Teltonika FOTA."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_ENABLED_SENSORS, SENSOR_KEYS, DOMAIN
from .coordinator import TeltonikaFotaCoordinator, TeltonikaFotaData


@dataclass(frozen=True, kw_only=True)
class TeltonikaFotaDeviceSensorEntityDescription(SensorEntityDescription):
    """Describes a Teltonika FOTA device sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, kw_only=True)
class TeltonikaFotaAccountSensorEntityDescription(SensorEntityDescription):
    """Describes a Teltonika FOTA account-level sensor entity."""

    value_fn: Callable[[TeltonikaFotaData], Any]


def _get_firmware_version(device: dict[str, Any]) -> str | None:
    """Extract firmware version from device data."""
    # Try multiple possible field names (current_firmware is the actual API field)
    for field in ("current_firmware", "firmware", "firmware_version", "fw_version", "fw", "version"):
        value = device.get(field)
        if value:
            if isinstance(value, dict):
                return value.get("version") or value.get("name")
            return str(value)

    return None


def _get_last_connection(device: dict[str, Any]) -> datetime | None:
    """Extract and parse last connection timestamp."""
    # Try multiple possible field names (seen_at is the actual API field)
    last_conn = None
    for field in ("seen_at", "last_connection", "last_update", "lastConnection", "last_seen", "updated_at"):
        if device.get(field):
            last_conn = device.get(field)
            break

    if last_conn:
        try:
            # Handle both string and datetime
            if isinstance(last_conn, datetime):
                parsed = last_conn
            else:
                # Parse datetime string (format: "2025-12-07 09:20:38")
                date_str = str(last_conn)
                parsed = dt_util.parse_datetime(date_str)

                # If parse_datetime fails, try manual parsing
                if parsed is None:
                    from datetime import datetime as dt
                    try:
                        parsed = dt.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        return None

            if parsed is None:
                return None

            # Ensure timezone is set (assume UTC if missing)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt_util.UTC)

            return parsed
        except (ValueError, TypeError):
            return None
    return None


def _get_device_name(device: dict[str, Any], imei: str) -> str:
    """Get device name from description + IMEI."""
    # Try to get description
    description = None
    for field in ("description", "name", "title", "label", "alias"):
        if device.get(field):
            description = str(device.get(field)).strip()
            break

    if description:
        return f"{description} ({imei})"

    # Fallback to just IMEI if no description
    return f"Teltonika ({imei})"


def _has_pending_tasks(device: dict[str, Any]) -> str:
    """Check if device has pending tasks, return Yes/No."""
    task_queue = device.get("task_queue")
    if task_queue and task_queue != "Empty":
        return "Yes"
    return "No"


# Device-level sensors (one per device/IMEI)
DEVICE_SENSORS: tuple[TeltonikaFotaDeviceSensorEntityDescription, ...] = (
    TeltonikaFotaDeviceSensorEntityDescription(
        key="activity_status",
        translation_key="activity_status",
        icon="mdi:signal",
        value_fn=lambda d: d.get("activity_status", "unknown"),
    ),
    TeltonikaFotaDeviceSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:package-variant",
        value_fn=_get_firmware_version,
    ),
    TeltonikaFotaDeviceSensorEntityDescription(
        key="task_queue_count",
        translation_key="task_queue_count",
        icon="mdi:format-list-numbered",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda d: 0 if d.get("task_queue") in (None, "Empty") else (
            len(d.get("task_queue")) if isinstance(d.get("task_queue"), list) else 1
        ),
    ),
    TeltonikaFotaDeviceSensorEntityDescription(
        key="model",
        translation_key="model",
        icon="mdi:router-wireless",
        value_fn=lambda d: d.get("model", "Unknown"),
    ),
    TeltonikaFotaDeviceSensorEntityDescription(
        key="last_connection",
        translation_key="last_connection",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
        value_fn=_get_last_connection,
    ),
    TeltonikaFotaDeviceSensorEntityDescription(
        key="has_pending_tasks",
        translation_key="has_pending_tasks",
        icon="mdi:clipboard-list",
        value_fn=_has_pending_tasks,
    ),
)

# Account-level sensors (one per integration)
ACCOUNT_SENSORS: tuple[TeltonikaFotaAccountSensorEntityDescription, ...] = (
    TeltonikaFotaAccountSensorEntityDescription(
        key="total_devices",
        translation_key="total_devices",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="devices",
        value_fn=lambda data: data.total_devices,
    ),
    TeltonikaFotaAccountSensorEntityDescription(
        key="online_devices",
        translation_key="online_devices",
        icon="mdi:access-point-check",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="devices",
        value_fn=lambda data: data.online_devices,
    ),
    TeltonikaFotaAccountSensorEntityDescription(
        key="offline_devices",
        translation_key="offline_devices",
        icon="mdi:access-point-off",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="devices",
        value_fn=lambda data: data.offline_devices,
    ),
    TeltonikaFotaAccountSensorEntityDescription(
        key="pending_tasks",
        translation_key="pending_tasks",
        icon="mdi:progress-clock",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda data: data.pending_tasks,
    ),
    TeltonikaFotaAccountSensorEntityDescription(
        key="failed_tasks",
        translation_key="failed_tasks",
        icon="mdi:alert-circle",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda data: data.failed_tasks,
    ),
    TeltonikaFotaAccountSensorEntityDescription(
        key="group_count",
        translation_key="group_count",
        icon="mdi:folder-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="groups",
        value_fn=lambda data: data.group_count,
    ),
    TeltonikaFotaAccountSensorEntityDescription(
        key="task_count",
        translation_key="task_count",
        icon="mdi:format-list-checks",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="tasks",
        value_fn=lambda data: data.task_count,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika FOTA sensors."""
    coordinator: TeltonikaFotaCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    # Get enabled sensors from options (default to all sensors)
    enabled_sensors = entry.options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS.keys()))

    entities: list[SensorEntity] = []

    # Add device-level sensors for each device (only enabled ones)
    for imei, device_data in coordinator.data.devices.items():
        for description in DEVICE_SENSORS:
            if description.key in enabled_sensors:
                entities.append(
                    TeltonikaFotaDeviceSensor(
                        coordinator,
                        entry,
                        imei,
                        device_data,
                        description,
                    )
                )

    # Add account-level sensors
    for description in ACCOUNT_SENSORS:
        entities.append(
            TeltonikaFotaAccountSensor(
                coordinator,
                entry,
                description,
            )
        )

    async_add_entities(entities)


class TeltonikaFotaDeviceSensor(
    CoordinatorEntity[TeltonikaFotaCoordinator],
    SensorEntity,
):
    """Representation of a Teltonika FOTA device sensor."""

    entity_description: TeltonikaFotaDeviceSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeltonikaFotaCoordinator,
        entry: ConfigEntry,
        imei: str,
        device_data: dict[str, Any],
        description: TeltonikaFotaDeviceSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._imei = imei
        self._entry = entry

        # Unique ID: domain_imei_sensorkey
        self._attr_unique_id = f"{DOMAIN}_{imei}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.data.devices.get(self._imei, {})
        model = device.get("model", "Unknown Device")
        firmware = _get_firmware_version(device)
        device_name = _get_device_name(device, self._imei)

        return DeviceInfo(
            identifiers={(DOMAIN, self._imei)},
            name=device_name,
            manufacturer="Teltonika",
            model=model,
            sw_version=firmware,
            configuration_url="https://fota.teltonika.lt",
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        device = self.coordinator.data.devices.get(self._imei, {})
        return self.entity_description.value_fn(device)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.data.devices.get(self._imei, {})
        attrs = {
            "imei": self._imei,
            "serial_number": device.get("serial"),
        }

        # Add task details for task_queue_count sensor
        if self.entity_description.key == "task_queue_count":
            task_queue = device.get("task_queue")
            if task_queue and task_queue != "Empty" and isinstance(task_queue, list):
                tasks = []
                for task in task_queue:
                    task_info = {
                        "id": task.get("id"),
                        "type": task.get("type"),
                        "status": task.get("status"),
                    }
                    tasks.append(task_info)
                attrs["tasks"] = tasks
                attrs["task_ids"] = [t.get("id") for t in task_queue if t.get("id")]

        return attrs


class TeltonikaFotaAccountSensor(
    CoordinatorEntity[TeltonikaFotaCoordinator],
    SensorEntity,
):
    """Representation of a Teltonika FOTA account-level sensor."""

    entity_description: TeltonikaFotaAccountSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeltonikaFotaCoordinator,
        entry: ConfigEntry,
        description: TeltonikaFotaAccountSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        # Unique ID for account-level sensors
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for the account 'device'."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"account_{self._entry.entry_id}")},
            name="Teltonika FOTA Account",
            manufacturer="Teltonika",
            model="FOTA Account",
            configuration_url="https://fota.teltonika.lt",
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs: dict[str, Any] = {}

        # Add task details for pending_tasks and failed_tasks sensors
        if self.entity_description.key in ("pending_tasks", "failed_tasks"):
            target_status = "pending" if self.entity_description.key == "pending_tasks" else "failed"
            tasks = []
            for task in self.coordinator.data.tasks:
                if task.get("status") == target_status:
                    task_info = {
                        "id": task.get("id"),
                        "type": task.get("type"),
                        "device_imei": task.get("imei"),
                        "status": task.get("status"),
                    }
                    tasks.append(task_info)
            if tasks:
                attrs["tasks"] = tasks
                attrs["task_ids"] = [t["id"] for t in tasks if t.get("id")]

        return attrs
