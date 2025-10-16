"""Support for Olarm alarm control panels.

Alarm control panels represent the areas on an alarm system that can be armed
and disarmed. Each area can be armed in different modes (away, home, night).
"""

from __future__ import annotations

import logging

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
        area_label: str,
    ) -> None:
        """Initialize the alarm control panel."""

        # Initialize base entity
        super().__init__(coordinator, device_id)

        # Store area-specific attributes
        self.area_index = area_index
        self.area_label = area_label

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
            area_state = areas[self.area_index]
            self._attr_alarm_state = STATE_MAP.get(
                area_state, AlarmControlPanelState.DISARMED
            )
        else:
            self._attr_alarm_state = AlarmControlPanelState.DISARMED

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

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        _LOGGER.debug("Disarming alarm area %s", self.area_index)
        await self.coordinator.send_area_disarm(self.device_id, self.area_index)
        # Set to pending state immediately for UI feedback
        self._attr_alarm_state = AlarmControlPanelState.PENDING
        self.async_write_ha_state()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        _LOGGER.debug("Arming away alarm area %s", self.area_index)
        await self.coordinator.send_area_arm(self.device_id, self.area_index)
        # Set to pending state immediately for UI feedback
        self._attr_alarm_state = AlarmControlPanelState.PENDING
        self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home (stay) command."""
        _LOGGER.debug("Arming home (stay) alarm area %s", self.area_index)
        await self.coordinator.send_area_stay(self.device_id, self.area_index)
        # Set to pending state immediately for UI feedback
        self._attr_alarm_state = AlarmControlPanelState.PENDING
        self.async_write_ha_state()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night (sleep) command."""
        _LOGGER.debug("Arming night (sleep) alarm area %s", self.area_index)
        await self.coordinator.send_area_sleep(self.device_id, self.area_index)
        # Set to pending state immediately for UI feedback
        self._attr_alarm_state = AlarmControlPanelState.PENDING
        self.async_write_ha_state()

