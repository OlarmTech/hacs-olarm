"""Support for Olarm alarm control panels.

An Olarm device connected to an alarm system can have upto 8 areas / partitions.
These can be armed, disarmed or partially armed.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import OlarmDataUpdateCoordinator
from .entity import OlarmEntity

_LOGGER = logging.getLogger(__name__)

# Mapping of Olarm area states to Home Assistant alarm states
STATE_MAP: dict[str, AlarmControlPanelState] = {
    "disarm": AlarmControlPanelState.DISARMED,
    "notready": AlarmControlPanelState.DISARMED,
    "stay": AlarmControlPanelState.ARMED_HOME,
    "arm": AlarmControlPanelState.ARMED_AWAY,
    "sleep": AlarmControlPanelState.ARMED_NIGHT,
    "alarm": AlarmControlPanelState.TRIGGERED,
    "emergency": AlarmControlPanelState.TRIGGERED,
    "fire": AlarmControlPanelState.TRIGGERED,
    "medical": AlarmControlPanelState.TRIGGERED,
    "partarm1": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "partarm2": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "partarm3": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "partarm4": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "stayarm1": AlarmControlPanelState.ARMED_HOME,
    "stayarm2": AlarmControlPanelState.ARMED_HOME,
    "stayarm3": AlarmControlPanelState.ARMED_HOME,
    "stayarm4": AlarmControlPanelState.ARMED_HOME,
    "entrydelay": AlarmControlPanelState.PENDING,
    "customarm1": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "customarm2": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "customarm3": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "customarm4": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Olarm alarm control panels for a config entry."""

    # get coordinator
    coordinator = config_entry.runtime_data.coordinator

    # load alarm control panels
    panels: list[OlarmAlarmControlPanel] = []
    load_area_panels(coordinator, config_entry, panels)

    async_add_entities(panels)


def load_area_panels(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    panels: list[OlarmAlarmControlPanel],
) -> None:
    """Load alarm control panel entities for each area."""
    device_id = config_entry.data["device_id"]
    areas = coordinator.data.device_state.get("areas", [])
    areas_labels = coordinator.data.device_profile.get("areasLabels", [])

    for area_index, area_state in enumerate(areas):
        area_label = (
            areas_labels[area_index]
            if area_index < len(areas_labels)
            else f"Area {area_index + 1}"
        )
        panels.append(
            OlarmAlarmControlPanel(
                coordinator,
                device_id,
                area_index,
                area_state,
                area_label,
            )
        )


class OlarmAlarmControlPanel(OlarmEntity, AlarmControlPanelEntity):
    """Define an Olarm alarm control panel."""

    _attr_code_arm_required = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(
        self,
        coordinator: OlarmDataUpdateCoordinator,
        device_id: str,
        area_index: int,
        area_state: str,
        area_label: str,
    ) -> None:
        """Initialize the alarm control panel."""

        # Initialize base entity
        super().__init__(coordinator, device_id)

        # Store area-specific attributes
        self.area_index = area_index
        self.area_label = area_label
        self.area_state = area_state

        # Set unique ID and name
        self._attr_unique_id = f"{device_id}.area.{area_index}"
        self._attr_name = f"Area {area_index + 1:02} - {area_label}"

        # Initialize alarm state
        self._update_alarm_state()

        _LOGGER.debug(
            "AlarmControlPanel: init %s -> %s",
            self._attr_name,
            self._attr_alarm_state,
        )

    def _update_alarm_state(self) -> None:
        """Update the alarm state from coordinator data."""
        if not self.coordinator.data:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED
            return

        areas = self.coordinator.data.device_state.get("areas", [])
        if self.area_index < len(areas):
            self.area_state = areas[self.area_index]
            self._attr_alarm_state = STATE_MAP.get(
                self.area_state, AlarmControlPanelState.DISARMED
            )
        else:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if self._attr_alarm_state == AlarmControlPanelState.ARMED_CUSTOM_BYPASS:
            return {"armed_custom_bypass_profile": self.area_state}
        return {"armed_custom_bypass_profile": None}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return

        # Store the previous state to check if it changed
        previous_state = self._attr_alarm_state

        # Update alarm state from coordinator data
        self._update_alarm_state()

        # Only schedule state update if the state actually changed
        if self._attr_alarm_state != previous_state:
            _LOGGER.debug(
                "AlarmControlPanel %s state changed: %s -> %s",
                self._attr_name,
                previous_state,
                self._attr_alarm_state,
            )
            self.async_write_ha_state()

    async def _async_send_command(self, command: str) -> None:
        """Send command and provide UI feedback."""
        _LOGGER.debug("AlarmControlPanel command: %s - %s", self._attr_name, command)

        await self.coordinator.send_command(
            command, self.device_id, self.area_index + 1
        )
        # Set to pending state for UI feedback while waiting for MQTT state to come through
        self._attr_alarm_state = AlarmControlPanelState.PENDING
        self.async_write_ha_state()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._async_send_command("area_disarm")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._async_send_command("area_arm")

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home (stay) command."""
        await self._async_send_command("area_stay")

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night (sleep) command."""
        await self._async_send_command("area_sleep")
