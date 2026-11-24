"""MQTT client wrapper for the Olarm integration."""

import logging
from typing import Any, Literal

from olarmflowclient import MqttConnectError, MqttTimeoutError, OlarmFlowClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util.ssl import get_default_context

from .const import DOMAIN
from .coordinator import OlarmDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class OlarmFlowClientMQTT:
    """MQTT client wrapper for Olarm devices.

    One connection carries the subscriptions of every device on the config
    entry. This class handles OAuth2 token refresh when the access token
    expires and routes incoming device messages to the matching coordinator.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        olarm_client: OlarmFlowClient,
        coordinators: dict[str, OlarmDataUpdateCoordinator],
    ) -> None:
        """Initialize the Olarm MQTT client wrapper."""

        self._hass: HomeAssistant = hass
        self._coordinators: dict[str, OlarmDataUpdateCoordinator] = coordinators
        # Any coordinator can refresh the shared OAuth2 session.
        self._coordinator: OlarmDataUpdateCoordinator = next(iter(coordinators.values()))
        self._entry_id: str = entry.entry_id

        self._user_id: str = entry.data["user_id"]
        self._olarm_flow_client: OlarmFlowClient = olarm_client

        # Default to "1" for backward compatibility with entries created before suffixes
        self.client_id_suffix: str = str(entry.data.get("client_id_suffix", "1"))

    async def _async_refresh_token(self) -> None:
        """Refresh the OAuth2 access token, logging instead of raising on failure."""
        try:
            await self._coordinator.async_ensure_token_valid()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("OAuth2: token refresh failed after MQTT status change")

    @property
    def _issue_id(self) -> str:
        """Issue registry id for this entry's MQTT connection."""
        return f"mqtt_disconnected_{self._entry_id}"

    def _mqtt_status_callback(
        self,
        status: Literal["connecting", "connected", "disconnected", "reconnecting"],
        info: dict[str, Any],
    ) -> None:
        """Handle MQTT connection status changes."""

        if status == "connecting":
            _LOGGER.debug("MQTT: connecting")
        elif status == "connected":
            _LOGGER.debug("MQTT: connected (%d device subscriptions)", len(self._coordinators))
            ir.async_delete_issue(self._hass, DOMAIN, self._issue_id)
        elif status == "disconnected":
            reason = info.get("reason", "Unknown reason")
            _LOGGER.error("MQTT: disconnected: %s", reason)
            # Use refresh token to fetch new access tokens if expired
            self._hass.async_create_task(self._async_refresh_token())
            ir.async_create_issue(
                self._hass,
                DOMAIN,
                self._issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="mqtt_disconnected",
                translation_placeholders={"reason": reason},
            )
        elif status == "reconnecting":
            reason = info.get("reason", "Unknown reason")
            _LOGGER.debug("MQTT: reconnecting: %s", reason)
            # Use refresh token to fetch new access tokens if expired
            self._hass.async_create_task(self._async_refresh_token())

    async def init_mqtt(self) -> None:
        """Initialize and connect to the Olarm MQTT service."""

        # Register before starting so the first connection includes the subscriptions
        self._olarm_flow_client.set_mqtt_status_callback(self._mqtt_status_callback)
        for device_id in self._coordinators:
            self._olarm_flow_client.subscribe_to_device(
                device_id,
                self._message_callback_for(device_id),
            )

        try:
            await self._coordinator.async_ensure_token_valid()

            await self._olarm_flow_client.start_mqtt_async(
                user_id=self._user_id,
                client_id_suffix=self.client_id_suffix,
                timeout=10.0,
                tls_context=get_default_context(),
            )
            _LOGGER.debug(
                "MQTT: subscribed to %d device(s): %s",
                len(self._coordinators),
                ", ".join(self._coordinators),
            )

        except (MqttTimeoutError, MqttConnectError) as e:
            _LOGGER.debug("MQTT: connection failed: %s", e)
            raise

    def _message_callback_for(self, device_id: str):
        """Build the MQTT callback for one device."""

        def _callback(topic: str, payload: dict[str, Any]) -> None:
            self.mqtt_message_callback(device_id, topic, payload)

        return _callback

    def mqtt_message_callback(
        self, device_id: str, topic: str, payload: dict[str, Any]
    ) -> None:
        """Handle incoming MQTT messages from an Olarm device."""

        _LOGGER.debug("MQTT: message received (device=%s, topic=%s)", device_id, topic)
        coordinator = self._coordinators.get(device_id)
        if coordinator is None:
            return
        coordinator.async_update_from_mqtt(payload)

    async def async_stop(self) -> None:
        """Stop the MQTT client and clean up connections."""
        self._olarm_flow_client.stop_mqtt()
        ir.async_delete_issue(self._hass, DOMAIN, self._issue_id)
