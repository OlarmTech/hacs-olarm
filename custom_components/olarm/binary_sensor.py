"""Support for Olarm binary sensors.

An Olarm device connected to an alarm system can have up to 192 zones, these are usually
door/window contacts and motion sensors. They can be either active or closed depending
if motion is detected or door/window is open.

The zones can also be bypassed so they are ignored if the alarm system is armed so
additional binary sensors are added for this. Alarm systems also monitor AC power
as they have battery backup so this is added as a binary sensor as well.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import OlarmDataUpdateCoordinator
from .entity import OlarmEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class OlarmBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an Olarm binary sensor entity."""

    value_fn: Callable[[OlarmDataUpdateCoordinator, int, str | None], bool]
    name_fn: Callable[[int, str], str]
    unique_id_fn: Callable[[str, int], str]


# Descriptions for the different Olarm binary sensor types
SENSOR_DESCRIPTIONS: dict[str, OlarmBinarySensorEntityDescription] = {
    "zone": OlarmBinarySensorEntityDescription(
        key="zone",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_state is not None
            and coord.data.device_state.get("zones", [])[index] == "a"
        ),
        name_fn=lambda index, label: f"Zone {index + 1:03} - {label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.zone.{index}",
    ),
    "zone_bypass": OlarmBinarySensorEntityDescription(
        key="zone_bypass",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_state is not None
            and coord.data.device_state.get("zones", [])[index] == "b"
        ),
        name_fn=lambda index, label: f"Zone {index + 1:03} Bypass - {label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.zone.bypass.{index}",
    ),
    "ac_power": OlarmBinarySensorEntityDescription(
        key="ac_power",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_state is not None
            and coord.data.device_state.get("powerAC") == "ok"
        ),
        name_fn=lambda index, label: f"{label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.ac_power",
    ),
    "link_input": OlarmBinarySensorEntityDescription(
        key="link_input",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_links is not None
            and link_id is not None
            and coord.data.device_links.get(link_id, {}).get("inputs", [])[index] == "high"
        ),
        name_fn=lambda index, label: f"LINK Input {index + 1:02} - {label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.link.input.{index}",
    ),
    "link_output": OlarmBinarySensorEntityDescription(
        key="link_output",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_links is not None
            and link_id is not None
            and coord.data.device_links.get(link_id, {}).get("outputs", [])[index] == "closed"
        ),
        name_fn=lambda index, label: f"LINK Output {index + 1:02} - {label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.link.output.{index}",
    ),
    "relay_output": OlarmBinarySensorEntityDescription(
        key="relay_output",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_links is not None
            and link_id is not None
            and coord.data.device_links.get(link_id, {}).get("relays", [])[index] == "latched"
        ),
        name_fn=lambda index, label: f"LINK Relay {index + 1:02} - {label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.link.relay.{index}",
    ),
    "max_input": OlarmBinarySensorEntityDescription(
        key="max_input",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_io is not None
            and coord.data.device_io.get("inputs", [])[index] == "high"
        ),
        name_fn=lambda index, label: f"MAX Input {index + 1:02} - {label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.max.input.{index}",
    ),
    "max_output": OlarmBinarySensorEntityDescription(
        key="max_output",
        value_fn=lambda coord, index, link_id: (
            coord.data is not None
            and coord.data.device_io is not None
            and coord.data.device_io.get("outputs", [])[index] == "closed"
        ),
        name_fn=lambda index, label: f"MAX Output {index + 1:02} - {label}",
        unique_id_fn=lambda device_id, index: f"{device_id}.max.output.{index}",
    ),
}

CLASS_MAP: dict[int, BinarySensorDeviceClass] = {
    10: BinarySensorDeviceClass.DOOR,
    11: BinarySensorDeviceClass.WINDOW,
    20: BinarySensorDeviceClass.MOTION,
    21: BinarySensorDeviceClass.MOTION,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add binary sensors for a config entry."""

    # get coordinator
    coordinator = config_entry.runtime_data.coordinator

    # load binary sensors
    sensors: list[OlarmBinarySensor] = []
    load_zone_sensors(coordinator, config_entry, sensors)
    load_ac_power_sensor(coordinator, config_entry, sensors)
    load_link_sensors(coordinator, config_entry, sensors)
    load_max_sensors(coordinator, config_entry, sensors)

    async_add_entities(sensors)


def load_zone_sensors(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    sensors: list[OlarmBinarySensor],
) -> None:
    """Load zone sensors and bypass sensors."""
    device_id = config_entry.data["device_id"]
    zones = coordinator.data.device_state.get("zones", [])
    labels = coordinator.data.device_profile.get("zonesLabels", [])
    types = coordinator.data.device_profile.get("zonesTypes", [])
    for zone_index, zone_state in enumerate(zones):
        zone_label = labels[zone_index] if zone_index < len(labels) else ""
        zone_class = types[zone_index] if zone_index < len(types) else 0
        sensors.extend(
            OlarmBinarySensor(
                coordinator,
                SENSOR_DESCRIPTIONS[sensor_type],
                device_id,
                zone_index,
                zone_state,
                zone_label,
                zone_class,
            )
            for sensor_type in ("zone", "zone_bypass")
        )


def load_ac_power_sensor(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    sensors: list[OlarmBinarySensor],
) -> None:
    """Load AC power sensor."""
    ac_power_state = (
        "on" if coordinator.data.device_state.get("powerAC") == "ok" else "off"
    )
    sensors.append(
        OlarmBinarySensor(
            coordinator,
            SENSOR_DESCRIPTIONS["ac_power"],
            config_entry.data["device_id"],
            0,
            ac_power_state,
            "AC Power",
            None,
        )
    )


def load_link_sensors(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    sensors: list[OlarmBinarySensor],
) -> None:
    """Load LINK inputs, outputs, and relays in latch mode."""
    if (
        coordinator.data.device_profile_links is None
        or len(coordinator.data.device_profile_links) == 0
        or coordinator.data.device_links is None
    ):
        return

    device_id = config_entry.data["device_id"]
    for link_id, link_data in coordinator.data.device_profile_links.items():
        link_name = link_data.get("name", "Unnamed Link")

        # Load IO items (inputs and outputs)
        io_items = link_data.get("io", [])
        for io_index, io in enumerate(io_items):
            # Only create sensors for enabled inputs/outputs
            if io.get("enabled"):
                if io.get("type") == "input":
                    io_state = coordinator.data.device_links[link_id]["inputs"][io_index]
                    sensors.append(
                        OlarmBinarySensor(
                            coordinator,
                            SENSOR_DESCRIPTIONS["link_input"],
                            f"{device_id}_{link_id}",
                            io_index,
                            io_state,
                            io.get("label", ""),
                            None,
                            link_id,
                            link_name,
                        )
                    )
                elif io.get("type") == "output" and io.get("outputMode") == "latch":
                    io_state = coordinator.data.device_links[link_id]["outputs"][io_index]
                    sensors.append(
                        OlarmBinarySensor(
                            coordinator,
                            SENSOR_DESCRIPTIONS["link_output"],
                            f"{device_id}_{link_id}",
                            io_index,
                            io_state,
                            io.get("label", ""),
                            None,
                            link_id,
                            link_name,
                        )
                    )

        # Load relay items
        relay_items = link_data.get("relays", [])
        for relay_index, relay in enumerate(relay_items):
            # Only create sensors for enabled relays in latch mode
            if relay.get("enabled") and relay.get("relayMode") == "latch":
                relay_state = coordinator.data.device_links[link_id]["relays"][relay_index]
                sensors.append(
                    OlarmBinarySensor(
                        coordinator,
                        SENSOR_DESCRIPTIONS["relay_output"],
                        f"{device_id}_{link_id}",
                        relay_index,
                        relay_state,
                        relay.get("label", ""),
                        None,
                        link_id,
                        link_name,
                    )
                )


def load_max_sensors(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    sensors: list[OlarmBinarySensor],
) -> None:
    """Load Max IO inputs and outputs (outputs only in latch mode)."""
    if (
        coordinator.data.device_profile_io is None
        or coordinator.data.device_profile_io.get("io") is None
        or coordinator.data.device_io is None
    ):
        return

    device_id = config_entry.data["device_id"]
    for io_index, io in enumerate(coordinator.data.device_profile_io.get("io")):
        if io.get("enabled"):
            if io.get("type") == "input":
                io_state = coordinator.data.device_io["inputs"][io_index]
                sensors.append(
                    OlarmBinarySensor(
                        coordinator,
                        SENSOR_DESCRIPTIONS["max_input"],
                        device_id,
                        io_index,
                        io_state,
                        io.get("label", ""),
                        None,
                    )
                )
            elif io.get("type") == "output" and io.get("outputMode") == "latch":
                io_state = coordinator.data.device_io["outputs"][io_index]
                sensors.append(
                    OlarmBinarySensor(
                        coordinator,
                        SENSOR_DESCRIPTIONS["max_output"],
                        device_id,
                        io_index,
                        io_state,
                        io.get("label", ""),
                        None,
                    )
                )


class OlarmBinarySensor(OlarmEntity, BinarySensorEntity):
    """Define an Olarm Binary Sensor."""

    entity_description: OlarmBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: OlarmDataUpdateCoordinator,
        description: OlarmBinarySensorEntityDescription,
        device_id: str,
        sensor_index: int,
        sensor_state: str,
        sensor_label: str,
        sensor_class: int | None = None,
        link_id: int | None = None,
        link_name: str | None = "",
    ) -> None:
        """Init the class."""

        # Initialize base entity
        super().__init__(coordinator, device_id)

        # store description
        self.entity_description = description

        # set attributes via description
        self._attr_translation_key = self.entity_description.key
        if self.entity_description.key in ("zone", "zone_bypass"):
            self._attr_translation_placeholders = {
                "zone_number": f"{sensor_index + 1:03}",
                "zone_label": " - " + sensor_label if sensor_label else "",
            }
        
        # For link/max sensors, override the name to include link_name
        if self.entity_description.key in ("link_input", "link_output", "relay_output"):
            self._attr_name = f"{link_name} {self.entity_description.name_fn(sensor_index, sensor_label)}"
        elif self.entity_description.key in ("max_input", "max_output"):
            self._attr_name = self.entity_description.name_fn(sensor_index, sensor_label)
        
        self._attr_unique_id = self.entity_description.unique_id_fn(
            device_id, sensor_index
        )

        _LOGGER.debug(
            "BinarySensor: init %s -> %s",
            self.entity_description.key,
            sensor_state,
        )

        # set the device class if provided
        if sensor_class in CLASS_MAP:
            self._attr_device_class = CLASS_MAP[sensor_class]

        # custom attributes
        self.sensor_index = sensor_index
        self.sensor_state = sensor_state
        self.sensor_label = sensor_label
        self.sensor_class = sensor_class
        self.link_id = (
            link_id  # only used for olarm LINKs to track which LINK as can have upto 8
        )

        # initialize state using description value_fn
        self._attr_is_on = self.entity_description.value_fn(
            self.coordinator, self.sensor_index, self.link_id
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return

        # Store the previous state to check if it changed
        previous_state = self._attr_is_on

        # Update state using description value_fn
        self._attr_is_on = self.entity_description.value_fn(
            self.coordinator, self.sensor_index, self.link_id
        )

        # Update sensor_state for zone sensors for extra attributes
        if self.entity_description.key in ("zone", "zone_bypass"):
            device_state = self.coordinator.data.device_state
            if device_state is not None:
                self.sensor_state = device_state.get("zones", [])[self.sensor_index]

        # Only schedule state update if the state actually changed
        if self._attr_is_on != previous_state:
            self.async_write_ha_state()
