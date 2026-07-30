"""The coordinator for the olarm integration to handle API and MQTT connections."""

from dataclasses import dataclass, field
import logging
from typing import Any, override

from aiohttp import ClientResponseError
from olarmflowclient import OlarmFlowClient, OlarmFlowClientApiError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryError,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class OlarmDeviceData:
    """Data structure to hold Olarm device information."""

    device_name: str
    device_alarm_type: str = ""
    device_alarm_type_actions: dict[str, Any] = field(default_factory=dict)
    device_state: dict[str, Any] = field(default_factory=dict)
    device_fence: dict[str, Any] = field(default_factory=dict)
    device_links: dict[str, Any] = field(default_factory=dict)
    device_io: dict[str, Any] = field(default_factory=dict)
    device_profile: dict[str, Any] = field(default_factory=dict)
    device_profile_links: dict[str, Any] = field(default_factory=dict)
    device_profile_io: dict[str, Any] = field(default_factory=dict)
    device_zone_in_alarms: dict[int, dict[str, Any]] = field(default_factory=dict)


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
        self._user_id = entry.data["user_id"]
        self.device_id = entry.data["device_id"]
        self._olarm_connect_client = olarm_client

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{self.device_id}",
            update_interval=None,  # No periodic updates, MQTT handles ongoing updates
        )

    async def _ensure_valid_token(self) -> None:
        """Ensure the OAuth2 access token is valid and refresh if needed.

        Checks if access token has expired and if not uses refresh token to fetch new.
        """
        token_valid: bool = self._oauth_session.valid_token
        if not token_valid:
            _LOGGER.debug("OAuth2: access token expired, refreshing")

        try:
            await self._oauth_session.async_ensure_token_valid()
            new_token: str = self._oauth_session.token["access_token"]
            expires_at: float = self._oauth_session.token["expires_at"]
            _LOGGER.debug("OAuth2: access token valid (expires_at=%s)", expires_at)

            await self._olarm_connect_client.update_access_token(new_token, expires_at)
        except ClientResponseError as e:
            # Status 400 (invalid_grant) indicates an expired/invalid refresh token
            if e.status == 400:
                _LOGGER.debug(
                    "OAuth2: refresh token invalid (status=%s): %s", e.status, e
                )
                raise ConfigEntryError(
                    "OAuth2 refresh token is invalid. Please remove and re-add the integration."
                ) from e

            # For other HTTP errors, treat as temporary and retry
            _LOGGER.debug("OAuth2: token refresh failed (status=%s): %s", e.status, e)
            raise ConfigEntryNotReady("Failed to refresh OAuth2 token") from e
        except Exception as e:
            _LOGGER.debug("OAuth2: token refresh failed: %s", e)
            raise ConfigEntryNotReady("Failed to refresh OAuth2 token") from e

    async def async_ensure_token_valid(self) -> None:
        """Public method to ensure token is valid before sending commands."""
        await self._ensure_valid_token()

    @override
    async def _async_update_data(self) -> OlarmDeviceData:
        """Fetch initial device information from the Olarm HTTP API."""
        try:
            device = await self._olarm_connect_client.get_device(self.device_id)
        except OlarmFlowClientApiError as e:
            raise UpdateFailed(f"Failed to reach Olarm API: {e}") from e
        else:
            device_data = OlarmDeviceData(
                device_name=device.get("deviceName") or "Olarm Device",
                device_alarm_type=device.get("deviceAlarmType") or "",
                device_alarm_type_actions=device.get("deviceAlarmTypeActions", {}),
                device_state=device.get("deviceState", {}),
                device_fence=device.get("deviceFence", {}),
                device_links=device.get("deviceLinks", {}),
                device_io=device.get("deviceIO", {}),
                device_profile=device.get("deviceProfile", {}),
                device_profile_links=device.get("deviceProfileLinks", {}),
                device_profile_io=device.get("deviceProfileIO", {}),
            )

            _LOGGER.debug(
                "API: fetched device (device_id=%s, name=%s)",
                self.device_id,
                device_data.device_name
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
        if "deviceFence" in payload:
            self.data.device_fence = payload["deviceFence"]
            updated = True
        if "deviceLinks" in payload:
            self.data.device_links = payload["deviceLinks"]
            updated = True
        if "deviceIO" in payload:
            self.data.device_io = payload["deviceIO"]
            updated = True

        if "deviceEvents" in payload:
            for event in payload["deviceEvents"]:
                if (
                    event.get("eventAction") == "zone_alarm"
                    and event.get("eventArea", 0) > 0
                ):
                    area: int = event["eventArea"]
                    # Olarm reports eventTime in epoch milliseconds; HA expects seconds
                    event_time = event.get("eventTime")
                    self.data.device_zone_in_alarms[area] = {
                        "zone": event.get("eventNum"),
                        "time": event_time / 1000 if event_time is not None else None,
                    }
                    updated = True

        if updated:
            self.async_set_updated_data(self.data)

    async def send_command(
        self,
        command: str,
        device_id: str,
        num: int = 0,
        link_id: str | None = None,
        part_num: int | None = None,
    ) -> dict[str, Any]:
        """Send a command to the Olarm API."""
        # Ensure token is valid before sending command
        await self.async_ensure_token_valid()

        # Construct the client method name from command
        client_method_name = f"send_{command}"
        client_fn = getattr(self._olarm_connect_client, client_method_name, None)

        if client_fn is None:
            raise ValueError(f"Unknown command: {command}")

        try:
            if link_id is not None:
                result = await client_fn(device_id, link_id, num)
            elif part_num is not None:
                result = await client_fn(device_id, num, part_num)
            elif num != 0:
                result = await client_fn(device_id, num)
            else:
                result = await client_fn(device_id)
        except OlarmFlowClientApiError as err:
            raise HomeAssistantError(f"Command '{command}' failed: {err}") from err

        return result or {}
