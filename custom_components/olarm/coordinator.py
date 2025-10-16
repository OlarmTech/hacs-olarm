"""The coordinator for the olarm integration to handle API and MQTT connections."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

from olarmflowclient import OlarmFlowClient, OlarmFlowClientApiError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class OlarmDeviceData:
    """Data structure to hold Olarm device information."""

    device_name: str
    device_state: dict[str, Any] = field(default_factory=dict)
    device_links: dict[str, Any] = field(default_factory=dict)
    device_io: dict[str, Any] = field(default_factory=dict)
    device_profile: dict[str, Any] = field(default_factory=dict)
    device_profile_links: dict[str, Any] = field(default_factory=dict)
    device_profile_io: dict[str, Any] = field(default_factory=dict)


class OlarmDataUpdateCoordinator(DataUpdateCoordinator[OlarmDeviceData]):
    """Manages data updates for an Olarm device.

    The initial state is fetched from the Olarm HTTP API and then subsequent updates
    are received via MQTT.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
        olarm_client: OlarmFlowClient,
    ) -> None:
        """Create a new instance of the OlarmCoordinator."""

        self._oauth_session = oauth_session

        # user props
        self._user_id = entry.data["user_id"]

        # device props
        self.device_id = entry.data["device_id"]

        # olarm connect client
        self._olarm_connect_client = olarm_client

        # Initialize DataUpdateCoordinator with no update interval (one-time setup only)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{self.device_id}",
            update_interval=None,  # No periodic updates, MQTT handles ongoing updates
        )

    async def _async_update_data(self) -> OlarmDeviceData:
        """Fetch initial device information from the Olarm HTTP API."""
        try:
            device = await self._olarm_connect_client.get_device(self.device_id)
        except OlarmFlowClientApiError as e:
            raise UpdateFailed("Failed to reach Olarm API") from e
        else:
            device_data = OlarmDeviceData(
                device_name=device.get("deviceName") or "Olarm Device",
                device_state=device.get("deviceState") or {},
                device_links=device.get("deviceLinks") or {},
                device_io=device.get("deviceIO") or {},
                device_profile=device.get("deviceProfile") or {},
                device_profile_links=device.get("deviceProfileLinks") or {},
                device_profile_io=device.get("deviceProfileIO") or {},
            )

            _LOGGER.debug(
                "Device -> %s",
                {
                    "device_name": device_data.device_name,
                    "device_state": device_data.device_state,
                },
            )

            return device_data

    def async_update_from_mqtt(self, payload: dict[str, Any]) -> None:
        """Handle subsequent updates from the Olarm MQTT Brokers.

        There are different MQTT payloads containing different state about the Olarm device
        so need to handle them appropriately.
        """
        if not self.data:
            return

        updated = False

        if "deviceState" in payload:
            self.data.device_state = payload["deviceState"]
            updated = True
        if "deviceLinks" in payload:
            self.data.device_links = payload["deviceLinks"]
            updated = True
        if "deviceIO" in payload:
            self.data.device_io = payload["deviceIO"]
            updated = True

        if updated:
            self.async_set_updated_data(self.data)

    # Command methods - delegate to the Olarm API client
    async def send_zone_bypass(self, device_id: str, zone_num: int) -> None:
        """Send zone bypass command."""
        await self._olarm_connect_client.send_device_zone_bypass(device_id, zone_num)

    async def send_zone_unbypass(self, device_id: str, zone_num: int) -> None:
        """Send zone unbypass command."""
        await self._olarm_connect_client.send_device_zone_unbypass(device_id, zone_num)

    async def send_pgm_open(self, device_id: str, pgm_num: int) -> None:
        """Send PGM open command."""
        await self._olarm_connect_client.send_device_pgm_open(device_id, pgm_num)

    async def send_pgm_close(self, device_id: str, pgm_num: int) -> None:
        """Send PGM close command."""
        await self._olarm_connect_client.send_device_pgm_close(device_id, pgm_num)

    async def send_pgm_pulse(self, device_id: str, pgm_num: int) -> None:
        """Send PGM pulse command."""
        await self._olarm_connect_client.send_device_pgm_pulse(device_id, pgm_num)

    async def send_ukey_activate(self, device_id: str, ukey_num: int) -> None:
        """Send utility key activate command."""
        await self._olarm_connect_client.send_device_ukey_activate(device_id, ukey_num)

    async def send_link_output_open(
        self, device_id: str, link_id: str, output_num: int
    ) -> None:
        """Send LINK output open command."""
        await self._olarm_connect_client.send_device_link_output_open(
            device_id, link_id, output_num
        )

    async def send_link_output_close(
        self, device_id: str, link_id: str, output_num: int
    ) -> None:
        """Send LINK output close command."""
        await self._olarm_connect_client.send_device_link_output_close(
            device_id, link_id, output_num
        )

    async def send_link_output_pulse(
        self, device_id: str, link_id: str, output_num: int
    ) -> None:
        """Send LINK output pulse command."""
        await self._olarm_connect_client.send_device_link_output_pulse(
            device_id, link_id, output_num
        )

    async def send_link_relay_unlatch(
        self, device_id: str, link_id: str, relay_num: int
    ) -> None:
        """Send LINK relay unlatch command."""
        await self._olarm_connect_client.send_device_link_relay_unlatch(
            device_id, link_id, relay_num
        )

    async def send_link_relay_latch(
        self, device_id: str, link_id: str, relay_num: int
    ) -> None:
        """Send LINK relay latch command."""
        await self._olarm_connect_client.send_device_link_relay_latch(
            device_id, link_id, relay_num
        )

    async def send_link_relay_pulse(
        self, device_id: str, link_id: str, relay_num: int
    ) -> None:
        """Send LINK relay pulse command."""
        await self._olarm_connect_client.send_device_link_relay_pulse(
            device_id, link_id, relay_num
        )

    async def send_max_output_open(self, device_id: str, output_num: int) -> None:
        """Send MAX output open command."""
        await self._olarm_connect_client.send_device_max_output_open(
            device_id, output_num
        )

    async def send_max_output_close(self, device_id: str, output_num: int) -> None:
        """Send MAX output close command."""
        await self._olarm_connect_client.send_device_max_output_close(
            device_id, output_num
        )

    async def send_max_output_pulse(self, device_id: str, output_num: int) -> None:
        """Send MAX output pulse command."""
        await self._olarm_connect_client.send_device_max_output_pulse(
            device_id, output_num
        )

    async def send_area_disarm(self, device_id: str, area_num: int) -> None:
        """Send area disarm command."""
        await self._olarm_connect_client.send_device_area_disarm(device_id, area_num)

    async def send_area_arm(self, device_id: str, area_num: int) -> None:
        """Send area arm away command."""
        await self._olarm_connect_client.send_device_area_arm(device_id, area_num)

    async def send_area_stay(self, device_id: str, area_num: int) -> None:
        """Send area arm home (stay) command."""
        await self._olarm_connect_client.send_device_area_stay(device_id, area_num)

    async def send_area_sleep(self, device_id: str, area_num: int) -> None:
        """Send area arm night (sleep) command."""
        await self._olarm_connect_client.send_device_area_sleep(device_id, area_num)
