"""Config flow for olarm integration."""

import logging
from typing import Any, override

from olarmflowclient import (
    DevicesNotFound,
    OlarmFlowClient,
    OlarmFlowClientApiError,
    OlarmFlowClientConnectionError,
    RateLimited,
    ServiceUnavailable,
    TokenExpired,
    Unauthorized,
)
import voluptuous as vol

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET

_LOGGER = logging.getLogger(__name__)

# Maps client exceptions to config flow abort reasons 
_API_ERROR_ABORT_REASONS: tuple[tuple[type[OlarmFlowClientApiError], str], ...] = (
    (TokenExpired, "token_expired"),
    (RateLimited, "rate_limited"),
    (Unauthorized, "unauthorized"),
    (OlarmFlowClientConnectionError, "cannot_connect"),
    (ServiceUnavailable, "service_unavailable"),
    (OlarmFlowClientApiError, "api_error"),
)


class OlarmOauth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for Olarm using OAuth2."""

    DOMAIN = DOMAIN

    _access_token: str | None = None
    _refresh_token: str | None = None
    _expires_at: int | None = None
    _user_id: str | None = None
    _devices: list[dict[str, Any]] | None = None
    _device_id: str | None = None
    _oauth_data: dict[str, Any] | None = None

    @property
    @override
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    @override
    def extra_authorize_data(self) -> dict[str, str]:
        """Extra data appended to the authorize URL. PKCE is handled automatically."""
        return {"scope": "email"}

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        # Import the default client credential for public OAuth client
        await async_import_client_credential(
            self.hass,
            DOMAIN,
            ClientCredential(OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET, name="Olarm"),
        )
        return await super().async_step_user()

    @override
    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow, or update existing entry."""
        self._oauth_data = data
        self._access_token = data["token"]["access_token"]
        self._refresh_token = data["token"]["refresh_token"]
        self._expires_at = data["token"]["expires_at"]

        _LOGGER.debug("OAuth2: tokens fetched, fetching devices")

        olarm_connect_client = OlarmFlowClient(self._access_token, self._expires_at)

        try:
            api_result = await olarm_connect_client.get_devices()
        except DevicesNotFound:
            return self.async_abort(reason="no_devices_found")
        except OlarmFlowClientApiError as err:
            reason = next(
                abort_reason
                for exc_type, abort_reason in _API_ERROR_ABORT_REASONS
                if isinstance(err, exc_type)
            )
            _LOGGER.debug("API: failed to fetch devices during setup: %s", err)
            return self.async_abort(
                reason=reason,
                description_placeholders={"error_detail": str(err)},
            )

        _LOGGER.debug("API: devices response: %s", api_result)
        self._devices = api_result.get("data")
        self._user_id = api_result.get("userId")
        return await self.async_step_device()

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the device selection step.

        A user can have many Olarms / devices so we need to ask them to select one for this home assistant instance
        """
        errors: dict[str, str] = {}
        if user_input is not None:
            self._device_id = user_input["select_device"]
            _LOGGER.debug("Config: device selected (device_id=%s)", self._device_id)

            if self._oauth_data is None:
                return self.async_abort(reason="oauth_data_missing")

            client_id_suffix = self._get_next_client_id_suffix()

            data = {
                "user_id": self._user_id,
                "device_id": self._device_id,
                "client_id_suffix": client_id_suffix,
                "auth_implementation": self._oauth_data["auth_implementation"],
                "token": self._oauth_data["token"],
            }

            unique_id = self._device_id
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title="Olarm Integration", data=data)

        if self._devices is None:
            return self.async_abort(reason="no_devices_found")

        device_options: dict[str, str] = {
            device["deviceId"]: f"{device['deviceName']} - {device['deviceSerial']}"
            for device in self._devices
        }
        sorted_device_options = dict(
            sorted(device_options.items(), key=lambda item: item[1])
        )
        schema = vol.Schema(
            {
                vol.Required("select_device"): vol.In(sorted_device_options),
            },
        )

        return self.async_show_form(step_id="device", data_schema=schema, errors=errors)

    def _get_next_client_id_suffix(self) -> str:
        """Get next available client_id_suffix."""
        used_suffixes = {
            int(entry.data.get("client_id_suffix", 0))
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.data.get("client_id_suffix")
        }

        for suffix in range(1, 101):
            if suffix not in used_suffixes:
                return str(suffix)

        # If all are used, cycle back to 1
        return "1"


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
