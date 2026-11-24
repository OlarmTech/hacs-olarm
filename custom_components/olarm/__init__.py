"""The olarm integration."""

from dataclasses import dataclass
import logging

from aiohttp import ClientError, ClientResponseError
from olarmflowclient import MqttConnectError, MqttTimeoutError, OlarmFlowClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .coordinator import OlarmDataUpdateCoordinator
from .mqtt import OlarmFlowClientMQTT


@dataclass(kw_only=True)
class OlarmData:
    """A class that holds runtime data."""

    coordinators: dict[str, OlarmDataUpdateCoordinator]
    mqtt_client: OlarmFlowClientMQTT

    @property
    def coordinator(self) -> OlarmDataUpdateCoordinator:
        """Return the first coordinator (backwards compatibility)."""
        return next(iter(self.coordinators.values()))


type OlarmConfigEntry = ConfigEntry[OlarmData]

_PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

_LOGGER = logging.getLogger(__name__)


def _entry_device_ids(entry: ConfigEntry) -> list[str]:
    """Return the device ids covered by a config entry.

    Entries created before multi-device support carry a single ``device_id``.
    """
    device_ids = entry.data.get("device_ids")
    if device_ids:
        return list(device_ids)
    device_id = entry.data.get("device_id")
    return [device_id] if device_id else []


async def async_setup_entry(hass: HomeAssistant, entry: OlarmConfigEntry) -> bool:
    """Set up olarm from a config entry."""

    device_ids = _entry_device_ids(entry)
    if not device_ids:
        raise ConfigEntryError("No Olarm devices configured for this entry")

    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    try:
        await session.async_ensure_token_valid()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryError("OAuth session not valid") from err
        raise ConfigEntryNotReady from err
    except ClientError as err:
        raise ConfigEntryNotReady from err
    _LOGGER.debug("OAuth2: session valid (expires_at=%s)", session.token["expires_at"])

    olarm_client = OlarmFlowClient(
        session.token["access_token"], session.token["expires_at"]
    )

    coordinators: dict[str, OlarmDataUpdateCoordinator] = {}
    for device_id in device_ids:
        coordinator = OlarmDataUpdateCoordinator(
            hass, entry, session, olarm_client, device_id
        )
        try:
            await coordinator.async_config_entry_first_refresh()
        except ConfigEntryNotReady as err:
            # One unreachable device (or one without API access) must not take
            # the whole entry down; surface it as a repair issue instead.
            _LOGGER.warning("API: skipping device %s: %s", device_id, err)
            ir.async_create_issue(
                hass,
                DOMAIN,
                f"device_unavailable_{device_id}",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="device_unavailable",
                translation_placeholders={"device_id": device_id},
            )
            continue
        ir.async_delete_issue(hass, DOMAIN, f"device_unavailable_{device_id}")
        coordinators[device_id] = coordinator

    if not coordinators:
        raise ConfigEntryNotReady("No Olarm devices could be loaded")

    mqtt_client = OlarmFlowClientMQTT(hass, entry, olarm_client, coordinators)
    try:
        await mqtt_client.init_mqtt()
    except (MqttTimeoutError, MqttConnectError) as err:
        raise ConfigEntryNotReady(f"Failed to connect to Olarm MQTT: {err}") from err

    entry.runtime_data = OlarmData(
        coordinators=coordinators,
        mqtt_client=mqtt_client,
    )

    # Normalise legacy single-device entries and make the account the unique id.
    updates: dict[str, object] = {}
    if "device_ids" not in entry.data:
        updates["data"] = {**entry.data, "device_ids": device_ids}
    if entry.unique_id != entry.data["user_id"]:
        updates["unique_id"] = entry.data["user_id"]
    if updates:
        try:
            hass.config_entries.async_update_entry(entry, **updates)
        except Exception:  # noqa: BLE001 - a failed migration must not break setup
            _LOGGER.exception("Config: could not migrate entry to multi-device")

    try:
        await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    except Exception:
        try:
            await mqtt_client.async_stop()
        except Exception:
            _LOGGER.exception("MQTT: error stopping client after failed setup")
        raise

    return True


async def async_unload_entry(hass: HomeAssistant, entry: OlarmConfigEntry) -> bool:
    """Unload a config entry."""
    mqtt_client = entry.runtime_data.mqtt_client

    # Stop mqtt - be defensive to ensure unload completes
    try:
        await mqtt_client.async_stop()
    except Exception:
        _LOGGER.exception("MQTT: error stopping client during unload")

    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
