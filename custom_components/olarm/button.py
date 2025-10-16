"""Support for Olarm buttons.

Buttons are used to control PGMs, zones (bypass/unbypass), utility keys,
LINK outputs/relays, and MAX outputs.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import OlarmDataUpdateCoordinator
from .entity import OlarmEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class OlarmButtonEntityDescription(ButtonEntityDescription):
    """Describes an Olarm button entity."""

    press_fn: Callable[
        [OlarmDataUpdateCoordinator, str, int, str | None], Coroutine[Any, Any, None]
    ]
    """Function to call when button is pressed."""

    name_fn: Callable[[int, str, str | None], str]
    """Function to generate button name."""

    unique_id_fn: Callable[[str, int, str | None], str]
    """Function to generate unique ID."""


# Button type descriptions
BUTTON_DESCRIPTIONS: dict[str, OlarmButtonEntityDescription] = {
    "zone_bypass": OlarmButtonEntityDescription(
        key="zone_bypass",
        press_fn=lambda coord, device_id, index, _: coord.send_zone_bypass(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"Zone {index + 1:03} Bypass - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.zone_bypass.{index}",
    ),
    "zone_unbypass": OlarmButtonEntityDescription(
        key="zone_unbypass",
        press_fn=lambda coord, device_id, index, _: coord.send_zone_unbypass(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"Zone {index + 1:03} Unbypass - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.zone_unbypass.{index}",
    ),
    "pgm_open": OlarmButtonEntityDescription(
        key="pgm_open",
        press_fn=lambda coord, device_id, index, _: coord.send_pgm_open(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"PGM {index + 1:02} Open - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.pgm_open.{index}",
    ),
    "pgm_close": OlarmButtonEntityDescription(
        key="pgm_close",
        press_fn=lambda coord, device_id, index, _: coord.send_pgm_close(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"PGM {index + 1:02} Close - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.pgm_close.{index}",
    ),
    "pgm_pulse": OlarmButtonEntityDescription(
        key="pgm_pulse",
        press_fn=lambda coord, device_id, index, _: coord.send_pgm_pulse(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"PGM {index + 1:02} Pulse - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.pgm_pulse.{index}",
    ),
    "ukey": OlarmButtonEntityDescription(
        key="ukey",
        press_fn=lambda coord, device_id, index, _: coord.send_ukey_activate(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"Utility Key {index + 1:02} - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.ukey.{index}",
    ),
    "link_output_open": OlarmButtonEntityDescription(
        key="link_output_open",
        press_fn=lambda coord, device_id, index, link_id: coord.send_link_output_open(
            device_id, link_id, index
        ),
        name_fn=lambda index, label, link_name: f"{link_name} Output {index + 1:02} Open - {label}",
        unique_id_fn=lambda device_id, index, link_id: f"{device_id}_{link_id}.link_output_open.{index}",
    ),
    "link_output_close": OlarmButtonEntityDescription(
        key="link_output_close",
        press_fn=lambda coord, device_id, index, link_id: coord.send_link_output_close(
            device_id, link_id, index
        ),
        name_fn=lambda index, label, link_name: f"{link_name} Output {index + 1:02} Close - {label}",
        unique_id_fn=lambda device_id, index, link_id: f"{device_id}_{link_id}.link_output_close.{index}",
    ),
    "link_output_pulse": OlarmButtonEntityDescription(
        key="link_output_pulse",
        press_fn=lambda coord, device_id, index, link_id: coord.send_link_output_pulse(
            device_id, link_id, index
        ),
        name_fn=lambda index, label, link_name: f"{link_name} Output {index + 1:02} Pulse - {label}",
        unique_id_fn=lambda device_id, index, link_id: f"{device_id}_{link_id}.link_output_pulse.{index}",
    ),
    "link_relay_unlatch": OlarmButtonEntityDescription(
        key="link_relay_unlatch",
        press_fn=lambda coord, device_id, index, link_id: coord.send_link_relay_unlatch(
            device_id, link_id, index
        ),
        name_fn=lambda index, label, link_name: f"{link_name} Relay {index + 1:02} Unlatch - {label}",
        unique_id_fn=lambda device_id, index, link_id: f"{device_id}_{link_id}.link_relay_unlatch.{index}",
    ),
    "link_relay_latch": OlarmButtonEntityDescription(
        key="link_relay_latch",
        press_fn=lambda coord, device_id, index, link_id: coord.send_link_relay_latch(
            device_id, link_id, index
        ),
        name_fn=lambda index, label, link_name: f"{link_name} Relay {index + 1:02} Latch - {label}",
        unique_id_fn=lambda device_id, index, link_id: f"{device_id}_{link_id}.link_relay_latch.{index}",
    ),
    "link_relay_pulse": OlarmButtonEntityDescription(
        key="link_relay_pulse",
        press_fn=lambda coord, device_id, index, link_id: coord.send_link_relay_pulse(
            device_id, link_id, index
        ),
        name_fn=lambda index, label, link_name: f"{link_name} Relay {index + 1:02} Pulse - {label}",
        unique_id_fn=lambda device_id, index, link_id: f"{device_id}_{link_id}.link_relay_pulse.{index}",
    ),
    "max_output_open": OlarmButtonEntityDescription(
        key="max_output_open",
        press_fn=lambda coord, device_id, index, _: coord.send_max_output_open(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"MAX Output {index + 1:02} Open - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.max_output_open.{index}",
    ),
    "max_output_close": OlarmButtonEntityDescription(
        key="max_output_close",
        press_fn=lambda coord, device_id, index, _: coord.send_max_output_close(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"MAX Output {index + 1:02} Close - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.max_output_close.{index}",
    ),
    "max_output_pulse": OlarmButtonEntityDescription(
        key="max_output_pulse",
        press_fn=lambda coord, device_id, index, _: coord.send_max_output_pulse(
            device_id, index
        ),
        name_fn=lambda index, label, _: f"MAX Output {index + 1:02} Pulse - {label}",
        unique_id_fn=lambda device_id, index, _: f"{device_id}.max_output_pulse.{index}",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add buttons for a config entry."""

    # get coordinator
    coordinator = config_entry.runtime_data.coordinator

    # init buttons
    buttons: list[OlarmButton] = []

    # load buttons based on device configuration
    load_zone_buttons(coordinator, config_entry, buttons)
    load_pgm_buttons(coordinator, config_entry, buttons)
    load_link_output_buttons(coordinator, config_entry, buttons)
    load_link_relay_buttons(coordinator, config_entry, buttons)
    load_max_output_buttons(coordinator, config_entry, buttons)

    async_add_entities(buttons)


def load_zone_buttons(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    buttons: list[OlarmButton],
) -> None:
    """Load zone bypass/unbypass buttons if enabled."""
    if not config_entry.data.get("load_zones_bypass_entities"):
        return

    device_id = config_entry.data["device_id"]
    zones = coordinator.data.device_state.get("zones", [])
    labels = coordinator.data.device_profile.get("zonesLabels", [])

    for zone_index, _ in enumerate(zones):
        zone_label = labels[zone_index] if zone_index < len(labels) else ""
        buttons.extend(
            [
                OlarmButton(
                    coordinator,
                    BUTTON_DESCRIPTIONS["zone_bypass"],
                    device_id,
                    zone_index,
                    zone_label,
                ),
                OlarmButton(
                    coordinator,
                    BUTTON_DESCRIPTIONS["zone_unbypass"],
                    device_id,
                    zone_index,
                    zone_label,
                ),
            ]
        )


def load_pgm_buttons(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    buttons: list[OlarmButton],
) -> None:
    """Load PGM and utility key buttons."""
    device_id = config_entry.data["device_id"]
    device_profile = coordinator.data.device_profile

    # Load PGM buttons
    pgm_controls = device_profile.get("pgmControl")
    if pgm_controls:
        pgm_labels = device_profile.get("pgmLabels", [])
        for pgm_index, pgm_control in enumerate(pgm_controls):
            if pgm_control[0] == "1":  # PGM is enabled
                pgm_label = (
                    pgm_labels[pgm_index] if pgm_index < len(pgm_labels) else ""
                )
                # Add open/close buttons
                if pgm_control[1] == "1":
                    buttons.extend(
                        [
                            OlarmButton(
                                coordinator,
                                BUTTON_DESCRIPTIONS["pgm_open"],
                                device_id,
                                pgm_index,
                                pgm_label,
                            ),
                            OlarmButton(
                                coordinator,
                                BUTTON_DESCRIPTIONS["pgm_close"],
                                device_id,
                                pgm_index,
                                pgm_label,
                            ),
                        ]
                    )
                # Add pulse button
                if pgm_control[2] == "1":
                    buttons.append(
                        OlarmButton(
                            coordinator,
                            BUTTON_DESCRIPTIONS["pgm_pulse"],
                            device_id,
                            pgm_index,
                            pgm_label,
                        )
                    )

    # Load utility key buttons
    ukeys_controls = device_profile.get("ukeysControl")
    if ukeys_controls:
        ukeys_labels = device_profile.get("ukeysLabels", [])
        for ukey_index, ukey_control in enumerate(ukeys_controls):
            if ukey_control == 1:  # Utility key is enabled
                ukey_label = (
                    ukeys_labels[ukey_index] if ukey_index < len(ukeys_labels) else ""
                )
                buttons.append(
                    OlarmButton(
                        coordinator,
                        BUTTON_DESCRIPTIONS["ukey"],
                        device_id,
                        ukey_index,
                        ukey_label,
                    )
                )


def load_link_output_buttons(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    buttons: list[OlarmButton],
) -> None:
    """Load LINK output buttons."""
    device_id = config_entry.data["device_id"]
    device_profile_links = coordinator.data.device_profile_links

    if not device_profile_links:
        return

    for link_id, link_data in device_profile_links.items():
        link_name = link_data.get("name", "Unnamed Link")
        io_outputs = link_data.get("io", [])

        for io_index, io in enumerate(io_outputs):
            # Only create buttons for enabled outputs
            if io.get("enabled") and io.get("type") == "output":
                io_label = io.get("label", "")
                output_mode = io.get("outputMode")

                # Add latch open/close buttons
                if output_mode == "latch":
                    buttons.extend(
                        [
                            OlarmButton(
                                coordinator,
                                BUTTON_DESCRIPTIONS["link_output_open"],
                                device_id,
                                io_index,
                                io_label,
                                link_id,
                                link_name,
                            ),
                            OlarmButton(
                                coordinator,
                                BUTTON_DESCRIPTIONS["link_output_close"],
                                device_id,
                                io_index,
                                io_label,
                                link_id,
                                link_name,
                            ),
                        ]
                    )
                # Add pulse button
                elif output_mode == "pulse":
                    buttons.append(
                        OlarmButton(
                            coordinator,
                            BUTTON_DESCRIPTIONS["link_output_pulse"],
                            device_id,
                            io_index,
                            io_label,
                            link_id,
                            link_name,
                        )
                    )


def load_link_relay_buttons(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    buttons: list[OlarmButton],
) -> None:
    """Load LINK relay buttons."""
    device_id = config_entry.data["device_id"]
    device_profile_links = coordinator.data.device_profile_links

    if not device_profile_links:
        return

    for link_id, link_data in device_profile_links.items():
        link_name = link_data.get("name", "Unnamed Link")
        relay_items = link_data.get("relays", [])

        for relay_index, relay in enumerate(relay_items):
            # Only create buttons for enabled relays
            if relay.get("enabled"):
                relay_label = relay.get("label", "")
                relay_mode = relay.get("relayMode")

                # Add latch/unlatch buttons
                if relay_mode == "latch":
                    buttons.extend(
                        [
                            OlarmButton(
                                coordinator,
                                BUTTON_DESCRIPTIONS["link_relay_unlatch"],
                                device_id,
                                relay_index,
                                relay_label,
                                link_id,
                                link_name,
                            ),
                            OlarmButton(
                                coordinator,
                                BUTTON_DESCRIPTIONS["link_relay_latch"],
                                device_id,
                                relay_index,
                                relay_label,
                                link_id,
                                link_name,
                            ),
                        ]
                    )
                # Add pulse button
                elif relay_mode == "pulse":
                    buttons.append(
                        OlarmButton(
                            coordinator,
                            BUTTON_DESCRIPTIONS["link_relay_pulse"],
                            device_id,
                            relay_index,
                            relay_label,
                            link_id,
                            link_name,
                        )
                    )


def load_max_output_buttons(
    coordinator: OlarmDataUpdateCoordinator,
    config_entry: ConfigEntry,
    buttons: list[OlarmButton],
) -> None:
    """Load MAX output buttons."""
    device_id = config_entry.data["device_id"]
    device_profile_io = coordinator.data.device_profile_io

    if not device_profile_io or not device_profile_io.get("io"):
        return

    for io_index, io in enumerate(device_profile_io.get("io", [])):
        # Only create buttons for enabled outputs
        if io.get("enabled") and io.get("type") == "output":
            io_label = io.get("label", "")
            output_mode = io.get("outputMode")

            # Add latch open/close buttons
            if output_mode == "latch":
                buttons.extend(
                    [
                        OlarmButton(
                            coordinator,
                            BUTTON_DESCRIPTIONS["max_output_open"],
                            device_id,
                            io_index,
                            io_label,
                        ),
                        OlarmButton(
                            coordinator,
                            BUTTON_DESCRIPTIONS["max_output_close"],
                            device_id,
                            io_index,
                            io_label,
                        ),
                    ]
                )
            # Add pulse button
            elif output_mode == "pulse":
                buttons.append(
                    OlarmButton(
                        coordinator,
                        BUTTON_DESCRIPTIONS["max_output_pulse"],
                        device_id,
                        io_index,
                        io_label,
                    )
                )


class OlarmButton(OlarmEntity, ButtonEntity):
    """Define an Olarm Button."""

    entity_description: OlarmButtonEntityDescription

    def __init__(
        self,
        coordinator: OlarmDataUpdateCoordinator,
        description: OlarmButtonEntityDescription,
        device_id: str,
        button_index: int,
        button_label: str,
        link_id: str | None = None,
        link_name: str | None = None,
    ) -> None:
        """Initialize the button."""

        # Initialize base entity
        super().__init__(coordinator, device_id)

        # Store description
        self.entity_description = description

        # Store button-specific attributes
        self.button_index = button_index
        self.button_label = button_label
        self.link_id = link_id
        self.link_name = link_name

        # Set unique ID and name using description functions
        self._attr_unique_id = self.entity_description.unique_id_fn(
            device_id, button_index, link_id
        )
        self._attr_name = self.entity_description.name_fn(
            button_index, button_label, link_name
        )

        _LOGGER.debug(
            "Button: init %s -> %s",
            self._attr_name,
            self.entity_description.key,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.entity_description.press_fn(
            self.coordinator, self.device_id, self.button_index, self.link_id
        )
        _LOGGER.debug(
            "Button pressed: %s [%s]",
            self._attr_name,
            self.entity_description.key,
        )


