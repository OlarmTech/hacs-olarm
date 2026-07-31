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

    This class manages the MQTT connection to Olarm's MQTT Brokers, handles OAuth2 token refresh
    when the access token expires and routes incoming device messages to the data coordinator.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        olarm_client: OlarmFlowClient,
        coordinator: OlarmDataUpdateCoordinator,
    ) -> None:
        """Initialize the Olarm MQTT client wrapper."""

        self._hass: HomeAssistant = hass
        self._coordinator: OlarmDataUpdateCoordinator = coordinator

        self._user_id: str = entry.data["user_id"]
        self.device_id: str = entry.data["device_id"]
        self._olarm_flow_client: OlarmFlowClient = olarm_client

        # Default to "1" for backward compatibility with entries created before suffixes
        self.client_id_suffix: str = str(entry.data.get("client_id_suffix", "1"))

    async def _async_refresh_token(self) -> None:
        """Refresh the OAuth2 access token, logging instead of raising on failure."""
        try:
            await self._coordinator.async_ensure_token_valid()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("OAuth2: token refresh failed after MQTT status change")

    def _mqtt_status_callback(
        self,
        status: Literal["connecting", "connected", "disconnected", "reconnecting"],
        info: dict[str, Any],
    ) -> None:
        """Handle MQTT connection status changes."""

        if status == "connecting":
            _LOGGER.debug("MQTT: connecting")
        elif status == "connected":
            _LOGGER.debug("MQTT: connected")
            ir.async_delete_issue(
                self._hass, DOMAIN, f"mqtt_disconnected_{self.device_id}"
            )
        elif status == "disconnected":
            reason = info.get("reason", "Unknown reason")
            _LOGGER.error("MQTT: disconnected: %s", reason)
            # Use refresh token to fetch new access tokens if expired
            self._hass.async_create_task(self._async_refresh_token())
            ir.async_create_issue(
                self._hass,
                DOMAIN,
                f"mqtt_disconnected_{self.device_id}",
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

        # Register before starting so the first connection includes the subscription
        self._olarm_flow_client.set_mqtt_status_callback(self._mqtt_status_callback)
        self._olarm_flow_client.subscribe_to_device(
            self.device_id, self.mqtt_message_callback
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
                "MQTT: subscribed to device updates (device_id=%s)", self.device_id
            )

        except (MqttTimeoutError, MqttConnectError) as e:
            _LOGGER.debug("MQTT: connection failed: %s", e)
            raise

    def mqtt_message_callback(self, topic: str, payload: dict[str, Any]) -> None:
        """Handle incoming MQTT messages from the Olarm device."""

        _LOGGER.debug("MQTT: message received (topic=%s): %s", topic, payload)
        self._coordinator.async_update_from_mqtt(payload)

    async def async_stop(self) -> None:
        """Stop the MQTT client and clean up connections."""
        self._olarm_flow_client.stop_mqtt()
        ir.async_delete_issue(
            self._hass, DOMAIN, f"mqtt_disconnected_{self.device_id}"
        )
