"""Tests for the GoodWe EntityAdapter — mode application and entity control.

Mirrors the foxess_control test_entity_mode.py patterns, adapted for the
GoodWe brand which is entity-mode only (no cloud API).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.goodwe_battery_control.smart_battery.adapter import (
    EntityAdapter,
)
from custom_components.goodwe_battery_control.smart_battery.types import WorkMode

from .conftest import GOODWE_MODE_MAP, make_adapter


class TestGetMaxPowerW:
    """Tests for adapter.get_max_power_w."""

    def test_returns_configured_power(self) -> None:
        adapter = make_adapter(max_power_w=5000)
        assert adapter.get_max_power_w() == 5000

    def test_returns_custom_power(self) -> None:
        adapter = make_adapter(max_power_w=8000)
        assert adapter.get_max_power_w() == 8000


class TestServiceDomain:
    """Tests for EntityAdapter._service_domain."""

    def test_select_entity_returns_select(self) -> None:
        assert EntityAdapter._service_domain("select.goodwe_mode", "select") == "select"

    def test_number_entity_returns_number(self) -> None:
        result = EntityAdapter._service_domain("number.goodwe_power", "number")
        assert result == "number"

    def test_input_select_entity_returns_input_select(self) -> None:
        assert (
            EntityAdapter._service_domain("input_select.inverter_mode", "select")
            == "input_select"
        )

    def test_input_number_entity_returns_input_number(self) -> None:
        assert (
            EntityAdapter._service_domain("input_number.charge_limit", "number")
            == "input_number"
        )

    def test_sensor_entity_returns_default(self) -> None:
        assert EntityAdapter._service_domain("sensor.something", "number") == "number"


class TestApplyMode:
    """Tests for EntityAdapter.apply_mode."""

    @pytest.mark.asyncio
    async def test_sets_self_use(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter()

        await adapter.apply_mode(hass, WorkMode.SELF_USE)

        hass.services.async_call.assert_called_once_with(
            "select",
            "select_option",
            {"entity_id": "select.goodwe_operation_mode", "option": "eco"},
        )

    @pytest.mark.asyncio
    async def test_sets_force_charge_with_power(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter()

        await adapter.apply_mode(hass, WorkMode.FORCE_CHARGE, power_w=3000)

        calls = hass.services.async_call.call_args_list
        assert len(calls) == 2
        # Work mode
        assert calls[0].args == (
            "select",
            "select_option",
            {"entity_id": "select.goodwe_operation_mode", "option": "eco_charge"},
        )
        # Power
        assert calls[1].args == (
            "number",
            "set_value",
            {"entity_id": "number.goodwe_charge_power", "value": 3000},
        )

    @pytest.mark.asyncio
    async def test_sets_force_discharge_with_power_and_min_soc(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter()

        await adapter.apply_mode(
            hass, WorkMode.FORCE_DISCHARGE, power_w=2500, fd_soc=20
        )

        calls = hass.services.async_call.call_args_list
        assert len(calls) == 3
        # Work mode → eco_discharge
        assert calls[0].args[2]["option"] == "eco_discharge"
        # Discharge power
        assert calls[1].args[2]["value"] == 2500
        assert calls[1].args[2]["entity_id"] == "number.goodwe_discharge_power"
        # Min SoC
        assert calls[2].args[2]["value"] == 20
        assert calls[2].args[2]["entity_id"] == "number.goodwe_min_soc"

    @pytest.mark.asyncio
    async def test_sets_feedin_mode(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter()

        await adapter.apply_mode(hass, WorkMode.FEEDIN, power_w=5000)

        # Feedin mode is set, but power is NOT — power only for charge/discharge
        assert hass.services.async_call.call_count == 1
        assert hass.services.async_call.call_args.args[2]["option"] == "peak_shaving"

    @pytest.mark.asyncio
    async def test_sets_backup_mode(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter()

        await adapter.apply_mode(hass, WorkMode.BACKUP)

        hass.services.async_call.assert_called_once_with(
            "select",
            "select_option",
            {"entity_id": "select.goodwe_operation_mode", "option": "backup"},
        )

    @pytest.mark.asyncio
    async def test_skips_power_when_no_entity_configured(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter(charge_power_entity=None)

        await adapter.apply_mode(hass, WorkMode.FORCE_CHARGE, power_w=5000)

        # Only work mode call — no charge_power_entity configured
        assert hass.services.async_call.call_count == 1

    @pytest.mark.asyncio
    async def test_skips_min_soc_when_no_entity_configured(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter(min_soc_entity=None)

        await adapter.apply_mode(
            hass, WorkMode.FORCE_DISCHARGE, power_w=3000, fd_soc=15
        )

        # Work mode + discharge power, but NO min SoC call
        assert hass.services.async_call.call_count == 2

    @pytest.mark.asyncio
    async def test_input_select_uses_correct_domain(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter(work_mode_entity="input_select.inverter_mode")

        await adapter.apply_mode(hass, WorkMode.SELF_USE)

        hass.services.async_call.assert_called_once_with(
            "input_select",
            "select_option",
            {"entity_id": "input_select.inverter_mode", "option": "eco"},
        )

    @pytest.mark.asyncio
    async def test_input_number_uses_correct_domain(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter(
            charge_power_entity="input_number.charge_limit",
        )

        await adapter.apply_mode(hass, WorkMode.FORCE_CHARGE, power_w=4000)

        calls = hass.services.async_call.call_args_list
        # Power call should use input_number domain
        assert calls[1].args[0] == "input_number"
        assert calls[1].args[1] == "set_value"

    @pytest.mark.asyncio
    async def test_all_goodwe_modes_in_mode_map(self) -> None:
        """Every WorkMode used by GoodWe must have a mapping."""
        expected_modes = {
            WorkMode.SELF_USE,
            WorkMode.FORCE_CHARGE,
            WorkMode.FORCE_DISCHARGE,
            WorkMode.BACKUP,
            WorkMode.FEEDIN,
        }
        assert set(GOODWE_MODE_MAP.keys()) == expected_modes


class TestRemoveOverride:
    """Tests for EntityAdapter.remove_override."""

    @pytest.mark.asyncio
    async def test_reverts_to_self_use(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter()

        await adapter.remove_override(hass, WorkMode.FORCE_CHARGE)

        hass.services.async_call.assert_called_once_with(
            "select",
            "select_option",
            {"entity_id": "select.goodwe_operation_mode", "option": "eco"},
        )

    @pytest.mark.asyncio
    async def test_reverts_from_discharge(self) -> None:
        hass = MagicMock()
        hass.services.async_call = AsyncMock()
        adapter = make_adapter()

        await adapter.remove_override(hass, WorkMode.FORCE_DISCHARGE)

        # Should set self-use (eco), regardless of what mode was active
        hass.services.async_call.assert_called_once_with(
            "select",
            "select_option",
            {"entity_id": "select.goodwe_operation_mode", "option": "eco"},
        )
