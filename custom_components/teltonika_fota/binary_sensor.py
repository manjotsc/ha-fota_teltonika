"""Binary sensor platform for Teltonika FOTA."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLED_SENSORS,
    SENSOR_KEYS,
    DOMAIN,
    STATUS_ONLINE,
    TASK_TYPE_FIRMWARE,
    TASK_STATUS_PENDING,
)
from .coordinator import TeltonikaFotaCoordinator
from .sensor import _get_firmware_version, _get_device_name


@dataclass(frozen=True, kw_only=True)
class TeltonikaFotaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Teltonika FOTA binary sensor entity."""

    is_on_fn: Callable[[dict[str, Any]], bool]


def _has_firmware_update_pending(device: dict[str, Any]) -> bool:
    """Check if device has a firmware update pending."""
    task_queue = device.get("task_queue")
    next_task = device.get("next_task")

    # Check next_task field for firmware updates
    if next_task and isinstance(next_task, dict):
        task_type = next_task.get("type", "")
        if "firmware" in str(task_type).lower():
            return True

    # Check task_queue if it's a list
    if task_queue and isinstance(task_queue, list):
        return any(
            "firmware" in str(t.get("type", "")).lower()
            for t in task_queue
        )

    return False


BINARY_SENSORS: tuple[TeltonikaFotaBinarySensorEntityDescription, ...] = (
    TeltonikaFotaBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda d: d.get("activity_status") == STATUS_ONLINE,
    ),
    TeltonikaFotaBinarySensorEntityDescription(
        key="firmware_update_pending",
        translation_key="firmware_update_pending",
        device_class=BinarySensorDeviceClass.UPDATE,
        is_on_fn=_has_firmware_update_pending,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Teltonika FOTA binary sensors."""
    coordinator: TeltonikaFotaCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    # Get enabled sensors from options (default to all sensors)
    enabled_sensors = entry.options.get(CONF_ENABLED_SENSORS, list(SENSOR_KEYS.keys()))

    entities: list[BinarySensorEntity] = []

    # Add binary sensors for each device (only enabled ones)
    for imei, device_data in coordinator.data.devices.items():
        for description in BINARY_SENSORS:
            if description.key in enabled_sensors:
                entities.append(
                    TeltonikaFotaBinarySensor(
                        coordinator,
                        entry,
                    imei,
                    device_data,
                    description,
                )
            )

    async_add_entities(entities)


class TeltonikaFotaBinarySensor(
    CoordinatorEntity[TeltonikaFotaCoordinator],
    BinarySensorEntity,
):
    """Representation of a Teltonika FOTA binary sensor."""

    entity_description: TeltonikaFotaBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeltonikaFotaCoordinator,
        entry: ConfigEntry,
        imei: str,
        device_data: dict[str, Any],
        description: TeltonikaFotaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._imei = imei
        self._entry = entry

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
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        device = self.coordinator.data.devices.get(self._imei, {})
        return self.entity_description.is_on_fn(device)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.data.devices.get(self._imei, {})
        return {
            "imei": self._imei,
            "serial_number": device.get("serial"),
        }
