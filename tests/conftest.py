"""Shared test fixtures for GoodWe Battery Control tests."""

from __future__ import annotations

import asyncio
import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from custom_components.goodwe_battery_control.const import (
    CONF_API_MIN_SOC,
    CONF_BATTERY_CAPACITY_KWH,
    CONF_CHARGE_POWER_ENTITY,
    CONF_DISCHARGE_POWER_ENTITY,
    CONF_MIN_POWER_CHANGE,
    CONF_MIN_SOC_ENTITY,
    CONF_MIN_SOC_ON_GRID,
    CONF_SMART_HEADROOM,
    CONF_WORK_MODE_ENTITY,
    DEFAULT_API_MIN_SOC,
    DEFAULT_GOODWE_INVERTER_POWER,
    DEFAULT_MIN_POWER_CHANGE,
    DEFAULT_MIN_SOC_ON_GRID,
    DEFAULT_SMART_HEADROOM,
    DOMAIN,
)
from custom_components.goodwe_battery_control.smart_battery.adapter import EntityAdapter
from custom_components.goodwe_battery_control.smart_battery.domain_data import (
    EntryData,
    SmartBatteryDomainData,
)
from custom_components.goodwe_battery_control.smart_battery.types import WorkMode

# GoodWe mode map — must match __init__.py
GOODWE_MODE_MAP: dict[WorkMode, str] = {
    WorkMode.SELF_USE: "eco",
    WorkMode.FORCE_CHARGE: "eco_charge",
    WorkMode.FORCE_DISCHARGE: "eco_discharge",
    WorkMode.BACKUP: "backup",
    WorkMode.FEEDIN: "peak_shaving",
}


def make_adapter(
    *,
    work_mode_entity: str = "select.goodwe_operation_mode",
    charge_power_entity: str | None = "number.goodwe_charge_power",
    discharge_power_entity: str | None = "number.goodwe_discharge_power",
    min_soc_entity: str | None = "number.goodwe_min_soc",
    max_power_w: int = DEFAULT_GOODWE_INVERTER_POWER,
) -> EntityAdapter:
    """Create an EntityAdapter with typical GoodWe defaults."""
    return EntityAdapter(
        mode_map=GOODWE_MODE_MAP,
        work_mode_entity=work_mode_entity,
        charge_power_entity=charge_power_entity,
        discharge_power_entity=discharge_power_entity,
        min_soc_entity=min_soc_entity,
        max_power_w=max_power_w,
    )


def make_hass(
    entry_id: str = "entry1",
    *,
    adapter: EntityAdapter | None = None,
    min_soc_on_grid: int = DEFAULT_MIN_SOC_ON_GRID,
    battery_capacity_kwh: float = 0.0,
    min_power_change: int = DEFAULT_MIN_POWER_CHANGE,
    api_min_soc: int = DEFAULT_API_MIN_SOC,
    smart_headroom: int = DEFAULT_SMART_HEADROOM,
    coordinator_data: dict[str, Any] | None = None,
) -> MagicMock:
    """Create a mock hass with DOMAIN data populated.

    *coordinator_data* populates the coordinator mock's ``.data`` attribute.
    Pass ``None`` (default) to create a coordinator with no data, or a dict
    like ``{"SoC": 50.0}`` to simulate polled values.
    """
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *a: fn(*a))
    hass.async_create_task = MagicMock(
        side_effect=lambda coro, **_kw: asyncio.ensure_future(coro)
    )
    hass.services.async_call = AsyncMock()

    if adapter is None:
        adapter = make_adapter()

    mock_store = MagicMock()
    mock_store.async_load = AsyncMock(return_value={})
    mock_store.async_save = AsyncMock()

    mock_coordinator = MagicMock()
    mock_coordinator.data = coordinator_data
    mock_coordinator.update_interval = datetime.timedelta(seconds=30)

    # Mock config entry for options lookup
    mock_entry = MagicMock()
    mock_entry.entry_id = entry_id
    mock_entry.options = {
        CONF_WORK_MODE_ENTITY: "select.goodwe_operation_mode",
        CONF_CHARGE_POWER_ENTITY: "number.goodwe_charge_power",
        CONF_DISCHARGE_POWER_ENTITY: "number.goodwe_discharge_power",
        CONF_MIN_SOC_ENTITY: "number.goodwe_min_soc",
        CONF_MIN_SOC_ON_GRID: min_soc_on_grid,
        CONF_BATTERY_CAPACITY_KWH: battery_capacity_kwh,
        CONF_MIN_POWER_CHANGE: min_power_change,
        CONF_API_MIN_SOC: api_min_soc,
        CONF_SMART_HEADROOM: smart_headroom,
    }

    dd = SmartBatteryDomainData()
    dd.store = mock_store
    dd.entries[entry_id] = EntryData(
        coordinator=mock_coordinator,
        inverter=adapter,
        entry=mock_entry,
    )
    hass.data = {DOMAIN: dd}

    hass.config_entries.async_get_entry = MagicMock(return_value=mock_entry)

    return hass


def make_entry(entry_id: str = "entry1") -> MagicMock:
    """Create a mock ConfigEntry."""
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.data = {}
    return entry


def make_call(data: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock ServiceCall."""
    call_mock = MagicMock()
    call_mock.data = data or {}
    return call_mock


def charge_state(**overrides: Any) -> dict[str, Any]:
    """Build a smart charge state dict with sensible defaults."""
    state: dict[str, Any] = {
        "target_soc": 80,
        "last_power_w": 4000,
        "max_power_w": DEFAULT_GOODWE_INVERTER_POWER,
        "start": datetime.datetime(2026, 4, 8, 2, 0, 0),
        "end": datetime.datetime(2026, 4, 8, 6, 0, 0),
        "charging_started": True,
    }
    state.update(overrides)
    return state


def discharge_state(**overrides: Any) -> dict[str, Any]:
    """Build a smart discharge state dict with sensible defaults."""
    state: dict[str, Any] = {
        "min_soc": 30,
        "last_power_w": 3000,
        "start": datetime.datetime(2026, 4, 8, 17, 0, 0),
        "end": datetime.datetime(2026, 4, 8, 20, 0, 0),
    }
    state.update(overrides)
    return state
