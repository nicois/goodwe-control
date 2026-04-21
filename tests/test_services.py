"""Tests for GoodWe Battery Control service handlers and integration lifecycle.

Mirrors foxess_control test_services.py patterns, adapted for GoodWe's
entity-mode architecture (no cloud API, no schedule groups).
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.goodwe_battery_control import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.goodwe_battery_control.const import (
    CONF_WORK_MODE_ENTITY,
    DEFAULT_GOODWE_INVERTER_POWER,
    DOMAIN,
)
from custom_components.goodwe_battery_control.smart_battery.domain_data import (
    EntryData,
    SmartBatteryDomainData,
    get_domain_data,
)
from custom_components.goodwe_battery_control.smart_battery.services import (
    register_services,
)

from .conftest import make_call, make_hass


class TestSetupEntry:
    """Tests for async_setup_entry."""

    @pytest.mark.asyncio
    async def test_setup_registers_services(self) -> None:
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.services.async_call = AsyncMock()

        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value={})
        mock_store.async_save = AsyncMock()

        dd = SmartBatteryDomainData()
        dd.store = mock_store
        hass.data = {DOMAIN: dd}

        entry = MagicMock()
        entry.entry_id = "entry1"
        entry.data = {}
        entry.options = {
            CONF_WORK_MODE_ENTITY: "select.goodwe_operation_mode",
        }
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        with (
            patch(
                "custom_components.goodwe_battery_control.GoodWeEntityCoordinator",
            ) as mock_coord_cls,
            patch(
                "custom_components.goodwe_battery_control._register_card_frontend",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.goodwe_battery_control._register_websocket_api",
            ),
        ):
            mock_coord = MagicMock()
            mock_coord.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coord

            assert await async_setup_entry(hass, entry) is True

        assert DOMAIN in hass.data
        assert hass.services.async_register.call_count == 6
        hass.config_entries.async_forward_entry_setups.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_second_entry_does_not_reregister_services(self) -> None:
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.services.async_call = AsyncMock()
        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value={})
        mock_store.async_save = AsyncMock()
        dd = SmartBatteryDomainData()
        dd.store = mock_store
        dd.entries["existing"] = EntryData(
            coordinator=MagicMock(),
            inverter=MagicMock(),
        )
        hass.data = {DOMAIN: dd}

        entry = MagicMock()
        entry.entry_id = "entry2"
        entry.data = {}
        entry.options = {
            CONF_WORK_MODE_ENTITY: "select.goodwe_operation_mode",
        }
        entry.add_update_listener = MagicMock(return_value=MagicMock())
        entry.async_on_unload = MagicMock()

        with (
            patch(
                "custom_components.goodwe_battery_control.GoodWeEntityCoordinator",
            ) as mock_coord_cls,
        ):
            mock_coord = MagicMock()
            mock_coord.async_config_entry_first_refresh = AsyncMock()
            mock_coord_cls.return_value = mock_coord

            assert await async_setup_entry(hass, entry) is True

        # Services should NOT be registered again
        hass.services.async_register.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_fails_without_entity_map(self) -> None:
        """Setup should fail when no entity mappings are configured."""
        hass = MagicMock()
        dd = SmartBatteryDomainData()
        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value={})
        dd.store = mock_store
        hass.data = {DOMAIN: dd}

        entry = MagicMock()
        entry.entry_id = "entry1"
        entry.data = {}
        entry.options = {}  # No work mode entity → empty entity map

        assert await async_setup_entry(hass, entry) is False


class TestUnloadEntry:
    """Tests for async_unload_entry."""

    @pytest.mark.asyncio
    async def test_unload_last_entry_removes_services(self) -> None:
        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock()
        dd = SmartBatteryDomainData()
        dd.entries["entry1"] = EntryData(
            coordinator=MagicMock(),
            inverter=MagicMock(),
        )
        hass.data = {DOMAIN: dd}

        entry = MagicMock()
        entry.entry_id = "entry1"

        result = await async_unload_entry(hass, entry)

        assert result is True
        assert DOMAIN not in hass.data
        assert hass.services.async_remove.call_count == 6
        hass.config_entries.async_unload_platforms.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unload_non_last_entry_keeps_services(self) -> None:
        hass = MagicMock()
        hass.config_entries.async_unload_platforms = AsyncMock()
        dd = SmartBatteryDomainData()
        dd.entries["entry1"] = EntryData(inverter=MagicMock())
        dd.entries["entry2"] = EntryData(inverter=MagicMock())
        hass.data = {DOMAIN: dd}

        entry = MagicMock()
        entry.entry_id = "entry1"

        result = await async_unload_entry(hass, entry)

        assert result is True
        assert DOMAIN in hass.data
        hass.services.async_remove.assert_not_called()


class TestClearOverrides:
    """Tests for the clear_overrides service handler."""

    @pytest.mark.asyncio
    async def test_clear_overrides_reverts_to_self_use(self) -> None:
        hass = make_hass()
        dd = get_domain_data(hass, DOMAIN)
        register_services(hass, DOMAIN, dd.entries["entry1"].inverter)

        handler = hass.services.async_register.call_args_list[0].args[2]
        await handler(make_call({}))

        # Should call select.select_option with "eco" (self-use)
        hass.services.async_call.assert_called()
        mode_call = hass.services.async_call.call_args_list[0]
        assert mode_call.args[1] == "select_option"
        assert mode_call.args[2]["option"] == "eco"


class TestSmartChargeSetup:
    """Tests for smart_charge service handler session setup."""

    @pytest.mark.asyncio
    async def test_smart_charge_stores_session_state(self) -> None:
        hass = make_hass(
            coordinator_data={"SoC": 30.0},
            battery_capacity_kwh=10.0,
        )
        dd = get_domain_data(hass, DOMAIN)
        register_services(hass, DOMAIN, dd.entries["entry1"].inverter)

        handler = hass.services.async_register.call_args_list[4].args[2]
        with patch(
            "custom_components.goodwe_battery_control.smart_battery.services.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = datetime.datetime(
                2026, 4, 8, 1, 0, 0, tzinfo=datetime.UTC
            )
            await handler(
                make_call(
                    {
                        "start_time": datetime.time(2, 0),
                        "end_time": datetime.time(6, 0),
                        "target_soc": 80,
                    }
                )
            )

        state = dd.smart_charge_state
        assert state is not None
        assert state["target_soc"] == 80

    @pytest.mark.asyncio
    async def test_smart_charge_registers_listeners(self) -> None:
        hass = make_hass(
            coordinator_data={"SoC": 30.0},
            battery_capacity_kwh=10.0,
        )
        dd = get_domain_data(hass, DOMAIN)
        register_services(hass, DOMAIN, dd.entries["entry1"].inverter)

        handler = hass.services.async_register.call_args_list[4].args[2]
        with patch(
            "custom_components.goodwe_battery_control.smart_battery.services.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = datetime.datetime(
                2026, 4, 8, 1, 0, 0, tzinfo=datetime.UTC
            )
            await handler(
                make_call(
                    {
                        "start_time": datetime.time(2, 0),
                        "end_time": datetime.time(6, 0),
                        "target_soc": 80,
                    }
                )
            )

        assert len(dd.smart_charge_unsubs) >= 2


class TestSmartDischargeSetup:
    """Tests for smart_discharge service handler session setup."""

    @pytest.mark.asyncio
    async def test_smart_discharge_stores_session_state(self) -> None:
        hass = make_hass(
            coordinator_data={"SoC": 80.0},
            battery_capacity_kwh=10.0,
        )
        dd = get_domain_data(hass, DOMAIN)
        register_services(hass, DOMAIN, dd.entries["entry1"].inverter)

        handler = hass.services.async_register.call_args_list[5].args[2]
        with patch(
            "custom_components.goodwe_battery_control.smart_battery.services.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = datetime.datetime(
                2026, 4, 8, 16, 0, 0, tzinfo=datetime.UTC
            )
            await handler(
                make_call(
                    {
                        "start_time": datetime.time(17, 0),
                        "end_time": datetime.time(20, 0),
                        "min_soc": 30,
                    }
                )
            )

        state = dd.smart_discharge_state
        assert state is not None
        assert state["min_soc"] == 30

    @pytest.mark.asyncio
    async def test_smart_discharge_respects_max_power(self) -> None:
        """Discharge power should not exceed adapter's max_power_w."""
        hass = make_hass(
            coordinator_data={"SoC": 80.0},
            battery_capacity_kwh=10.0,
        )
        dd = get_domain_data(hass, DOMAIN)
        register_services(hass, DOMAIN, dd.entries["entry1"].inverter)

        handler = hass.services.async_register.call_args_list[5].args[2]
        with patch(
            "custom_components.goodwe_battery_control.smart_battery.services.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = datetime.datetime(
                2026, 4, 8, 16, 0, 0, tzinfo=datetime.UTC
            )
            await handler(
                make_call(
                    {
                        "start_time": datetime.time(17, 0),
                        "end_time": datetime.time(20, 0),
                        "min_soc": 30,
                    }
                )
            )

        state = dd.smart_discharge_state
        assert state is not None
        assert state["max_power_w"] == DEFAULT_GOODWE_INVERTER_POWER
