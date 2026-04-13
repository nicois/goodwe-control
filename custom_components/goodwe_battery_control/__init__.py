"""GoodWe Battery Control — Home Assistant integration for inverter mode management."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.helpers.storage import Store

from .const import (
    CONF_CHARGE_POWER_ENTITY,
    CONF_DISCHARGE_POWER_ENTITY,
    CONF_INVERTER_POWER,
    CONF_MIN_SOC_ENTITY,
    CONF_POLLING_INTERVAL,
    CONF_WORK_MODE_ENTITY,
    DEFAULT_ENTITY_POLLING_INTERVAL,
    DEFAULT_GOODWE_INVERTER_POWER,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import GoodWeEntityCoordinator
from .smart_battery.adapter import EntityAdapter
from .smart_battery.config_flow_base import build_entity_map
from .smart_battery.const import (
    SERVICE_CLEAR_OVERRIDES,
    SERVICE_FEEDIN,
    SERVICE_FORCE_CHARGE,
    SERVICE_FORCE_DISCHARGE,
    SERVICE_SMART_CHARGE,
    SERVICE_SMART_DISCHARGE,
    STORAGE_VERSION,
)
from .smart_battery.services import register_services
from .smart_battery.types import WorkMode

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "goodwe_battery_control_sessions"

# GoodWe mode names as exposed by the home-assistant-goodwe-inverter integration.
_GOODWE_MODE_MAP: dict[WorkMode, str] = {
    WorkMode.SELF_USE: "eco",
    WorkMode.FORCE_CHARGE: "eco_charge",
    WorkMode.FORCE_DISCHARGE: "eco_discharge",
    WorkMode.BACKUP: "backup",
    WorkMode.FEEDIN: "peak_shaving",
}


_ENTITY_ROLES: dict[str, str] = {
    "smart_operations": "smart_operations",
    "battery_forecast": "battery_forecast",
}

_CARD_URLS = [
    f"/{DOMAIN}/goodwe-control-card.js",
    f"/{DOMAIN}/goodwe-overview-card.js",
]


def _register_websocket_api(hass: HomeAssistant) -> None:
    """Register WebSocket commands for Lovelace card entity discovery."""
    from homeassistant.components.websocket_api import (  # type: ignore[attr-defined]
        async_register_command,
        async_response,
        websocket_command,
    )
    from homeassistant.helpers import entity_registry as er

    @websocket_command({vol.Required("type"): f"{DOMAIN}/entity_map"})
    @async_response
    async def ws_entity_map(
        hass: HomeAssistant,
        connection: Any,
        msg: dict[str, Any],
    ) -> None:
        """Return a role->entity_id mapping for goodwe_battery_control entities."""
        registry = er.async_get(hass)
        entry_id: str | None = None
        for key in hass.data.get(DOMAIN, {}):
            if not str(key).startswith("_"):
                entry_id = key
                break

        result: dict[str, str] = {}
        if entry_id is not None:
            entries = er.async_entries_for_config_entry(registry, entry_id)
            suffix_map: dict[str, str] = {}
            for ent in entries:
                for suffix in _ENTITY_ROLES.values():
                    if ent.unique_id.endswith(f"_{suffix}"):
                        suffix_map[suffix] = ent.entity_id
                        break
            for role, suffix in _ENTITY_ROLES.items():
                if suffix in suffix_map:
                    result[role] = suffix_map[suffix]

            # Also expose user-configured entities from the coordinator
            domain_data = hass.data.get(DOMAIN, {})
            entry_data = domain_data.get(entry_id, {})
            coordinator = entry_data.get("coordinator")
            if coordinator is not None:
                emap = getattr(coordinator, "_entity_map", {})
                role_from_key = {
                    "soc_entity": "battery_soc",
                    "loads_power_entity": "house_load",
                    "pv_power_entity": "solar_power",
                }
                for key, role in role_from_key.items():
                    eid = emap.get(key)
                    if eid:
                        result[role] = eid

        connection.send_result(msg["id"], result)

    async_register_command(hass, ws_entity_map)


async def _register_card_frontend(hass: HomeAssistant) -> None:
    """Serve the custom Lovelace card JS files and register them as resources."""
    import json
    from pathlib import Path

    from homeassistant.components.http import StaticPathConfig

    card_dir = Path(__file__).parent
    static_paths = []
    for card_url in _CARD_URLS:
        filename = card_url.rsplit("/", 1)[-1]
        card_path = card_dir / "www" / filename
        static_paths.append(
            StaticPathConfig(card_url, str(card_path), cache_headers=True)
        )
    await hass.http.async_register_static_paths(static_paths)

    try:
        raw = await hass.async_add_executor_job(
            (card_dir / "manifest.json").read_text
        )
        manifest = json.loads(raw)
        version = manifest.get("version", "0")
    except Exception:
        version = "0"

    try:
        import importlib

        _ll_mod = importlib.import_module("homeassistant.components.lovelace")
        LOVELACE_DATA = _ll_mod.LOVELACE_DATA

        ll_data = hass.data.get(LOVELACE_DATA)
        if ll_data is not None and hasattr(ll_data.resources, "async_create_item"):
            for card_url in _CARD_URLS:
                versioned_url = f"{card_url}?v={version}"
                existing = [
                    r
                    for r in ll_data.resources.async_items()
                    if card_url in r.get("url", "")
                ]
                for r in existing:
                    if r.get("url") != versioned_url:
                        await ll_data.resources.async_delete_item(r["id"])
                current = [
                    r
                    for r in ll_data.resources.async_items()
                    if r.get("url") == versioned_url
                ]
                if not current:
                    await ll_data.resources.async_create_item(
                        {"res_type": "module", "url": versioned_url}
                    )
                    _LOGGER.info("Registered Lovelace resource: %s", versioned_url)
    except Exception:
        _LOGGER.debug(
            "Could not auto-register Lovelace resources; "
            "add them manually as module resources",
            exc_info=True,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GoodWe Battery Control from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("_smart_discharge_unsubs", [])
    hass.data[DOMAIN].setdefault("_smart_charge_unsubs", [])
    if "_store" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["_store"] = Store[dict[str, Any]](
            hass, STORAGE_VERSION, STORAGE_KEY
        )

    entity_map = build_entity_map(entry.options)
    if not entity_map:
        _LOGGER.error(
            "No entity mappings configured. Configure GoodWe entities in options."
        )
        return False

    polling_interval = int(
        entry.options.get(CONF_POLLING_INTERVAL, DEFAULT_ENTITY_POLLING_INTERVAL)
    )
    coordinator = GoodWeEntityCoordinator(hass, entity_map, polling_interval)
    await coordinator.async_config_entry_first_refresh()

    max_power = int(
        entry.options.get(CONF_INVERTER_POWER, DEFAULT_GOODWE_INVERTER_POWER)
    )
    adapter = EntityAdapter(
        mode_map=_GOODWE_MODE_MAP,
        work_mode_entity=entry.options[CONF_WORK_MODE_ENTITY],
        charge_power_entity=entry.options.get(CONF_CHARGE_POWER_ENTITY),
        discharge_power_entity=entry.options.get(CONF_DISCHARGE_POWER_ENTITY),
        min_soc_entity=entry.options.get(CONF_MIN_SOC_ENTITY),
        max_power_w=max_power,
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "adapter": adapter,
        "entry": entry,
    }

    # Register services, frontend card, and WS API once (first real entry)
    real_entries = {k for k in hass.data[DOMAIN] if not k.startswith("_")}
    if len(real_entries) == 1:
        register_services(hass, DOMAIN, adapter)
        _register_websocket_api(hass)
        await _register_card_frontend(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    hass.data[DOMAIN].pop(entry.entry_id)

    remaining = {k for k in hass.data[DOMAIN] if not k.startswith("_")}
    if not remaining:
        from .smart_battery.listeners import cancel_smart_charge, cancel_smart_discharge

        cancel_smart_charge(hass, DOMAIN, clear_storage=False)
        cancel_smart_discharge(hass, DOMAIN, clear_storage=False)
        hass.data.pop(DOMAIN)
        for svc in (
            SERVICE_CLEAR_OVERRIDES,
            SERVICE_FEEDIN,
            SERVICE_FORCE_CHARGE,
            SERVICE_FORCE_DISCHARGE,
            SERVICE_SMART_CHARGE,
            SERVICE_SMART_DISCHARGE,
        ):
            hass.services.async_remove(DOMAIN, svc)

    return True
