"""Support for Olarm alarm control panels.

An Olarm device connected to an alarm system can have upto 8 areas / partitions.
These can be armed, disarmed or partially armed.
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .coordinator import OlarmDataUpdateCoordinator
from .entity import OlarmEntity

_LOGGER = logging.getLogger(__name__)

# Time in seconds to wait for an MQTT state update after sending a command
# before reverting the optimistic pending state back to the actual area state.
PENDING_STATE_TIMEOUT = 10

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
    "countdown": AlarmControlPanelState.PENDING,
    "customarm1": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "customarm2": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "customarm3": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "customarm4": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
}

# Mapping of Olarm area action strings to HA alarm feature flags.
# "area-disarm" is intentionally excluded — disarm is always available in HA.
# Partial arm actions (area-part-arm-1 etc.) are exposed as button entities instead,
# since a single alarm panel entity can only have one custom bypass action but alarm
# systems may support up to 4 partial arming profiles per area.
ACTION_FEATURE_MAP: dict[str, AlarmControlPanelEntityFeature] = {
    "area-arm": AlarmControlPanelEntityFeature.ARM_AWAY,
    "area-stay": AlarmControlPanelEntityFeature.ARM_HOME,
    "area-sleep": AlarmControlPanelEntityFeature.ARM_NIGHT,
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

    _LOGGER.debug("AlarmControlPanel: adding %d entities", len(panels))
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
        self._pending_timeout_cancel: CALLBACK_TYPE | None = None

        # Set unique ID and name
        self._attr_unique_id = f"{device_id}.area.{area_index}"
        self._attr_name = f"Area {area_index + 1:02} - {area_label}"

        # Build supported features from the alarm type actions reported by the API
        area_actions: list[str] = coordinator.data.device_alarm_type_actions.get(
            "areas", []
        )
        features = AlarmControlPanelEntityFeature(0)
        for action in area_actions:
            if feature := ACTION_FEATURE_MAP.get(action):
                features |= feature
        self._attr_supported_features = features

        # Initialize alarm state
        self._update_alarm_state()

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
        attrs: dict[str, Any] = {}

        if self._attr_alarm_state == AlarmControlPanelState.ARMED_CUSTOM_BYPASS:
            attrs["armed_custom_bypass_profile"] = self.area_state
        else:
            attrs["armed_custom_bypass_profile"] = None

        # check if area has zone in alarms
        if self.coordinator.data:
            zone_data = self.coordinator.data.device_zone_in_alarms.get(
                self.area_index + 1, {}
            )
            attrs["zone_in_alarm"] = zone_data.get("zone")
            attrs["zone_in_alarm_time"] = zone_data.get("time")
        else:
            attrs["zone_in_alarm"] = None
            attrs["zone_in_alarm_time"] = None

        return attrs

    @callback
    def _cancel_pending_timeout(self) -> None:
        """Cancel the pending state timeout timer if active."""
        if self._pending_timeout_cancel is not None:
            self._pending_timeout_cancel()
            self._pending_timeout_cancel = None

    @callback
    def _async_pending_timeout(self, _now: datetime) -> None:
        """Reset pending state if no MQTT state change was received in time."""
        self._pending_timeout_cancel = None
        self._update_alarm_state()
        _LOGGER.debug(
            "AlarmControlPanel: pending state timed out, reverting (name=%s, area_state=%s, ha_state=%s)",
            self._attr_name,
            self.area_state,
            self._attr_alarm_state,
        )
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up pending timeout timer when entity is removed."""
        self._cancel_pending_timeout()
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return

        areas = self.coordinator.data.device_state.get("areas", [])
        new_area_state = (
            areas[self.area_index] if self.area_index < len(areas) else self.area_state
        )

        # If a command is currently awaiting an MQTT state transition and the area state
        # hasn't changed yet (e.g. an unrelated zone update arrived), keep the optimistic
        # pending state until either the area state changes or the timeout expires.
        if (
            self._pending_timeout_cancel is not None
            and new_area_state == self.area_state
        ):
            return

        # check if area_state has changed
        previous_area_state = self.area_state

        self._cancel_pending_timeout()
        self._update_alarm_state()

        if self.area_state != previous_area_state:
            _LOGGER.debug(
                "AlarmControlPanel: state changed (name=%s, from=%s, to=%s, ha_state=%s)",
                self._attr_name,
                previous_area_state,
                self.area_state,
                self._attr_alarm_state,
            )
            self.async_write_ha_state()

    async def _async_send_command(self, command: str) -> None:
        """Send command and provide UI feedback."""
        _LOGGER.debug(
            "AlarmControlPanel: sending command (name=%s, command=%s)",
            self._attr_name,
            command,
        )

        self._cancel_pending_timeout()
        area_state_before = self.area_state

        await self.coordinator.send_command(
            command, self.device_id, self.area_index + 1
        )

        # If an MQTT update already changed the area state while the command was in flight,
        # keep the updated state rather than overwriting it with PENDING.
        if self.area_state != area_state_before:
            return

        # If disarming when the area is already disarmed/notready in coordinator data
        # (e.g. cancelling a stuck/optimistic pending state), restore DISARMED immediately.
        if (
            command == "device_area_disarm"
            and STATE_MAP.get(self.area_state, AlarmControlPanelState.DISARMED)
            == AlarmControlPanelState.DISARMED
        ):
            self._update_alarm_state()
            self.async_write_ha_state()
            return

        # Set to pending state for UI feedback while waiting for MQTT state to come through,
        # and schedule a timeout to revert if the panel rejects or ignores the command.
        self._attr_alarm_state = AlarmControlPanelState.PENDING
        self._pending_timeout_cancel = async_call_later(
            self.hass, PENDING_STATE_TIMEOUT, self._async_pending_timeout
        )
        self.async_write_ha_state()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._async_send_command("device_area_disarm")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._async_send_command("device_area_arm")

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home (stay) command."""
        await self._async_send_command("device_area_stay")

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night (sleep) command."""
        await self._async_send_command("device_area_sleep")
