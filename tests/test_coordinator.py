"""Tests for the GoodWe entity-mode coordinator.

Mirrors foxess_control test_entity_mode.py TestEntityCoordinator, adapted
for the GoodWe coordinator which reads inverter state from HA entities.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from custom_components.goodwe_battery_control.coordinator import (
    GoodWeEntityCoordinator,
)


def _make_coordinator(entity_map: dict[str, str]) -> GoodWeEntityCoordinator:
    """Create a coordinator without running DataUpdateCoordinator.__init__."""
    with patch(
        "custom_components.goodwe_battery_control.coordinator."
        "EntityCoordinator.__init__"
    ):
        coord = GoodWeEntityCoordinator.__new__(GoodWeEntityCoordinator)
        coord.hass = MagicMock()
        coord._entity_map = entity_map
    return coord


class TestAsyncUpdateData:
    """Tests for GoodWeEntityCoordinator._async_update_data."""

    @pytest.mark.asyncio
    async def test_reads_entity_states(self) -> None:
        soc_state = MagicMock()
        soc_state.state = "75.5"
        loads_state = MagicMock()
        loads_state.state = "1.2"
        work_mode_state = MagicMock()
        work_mode_state.state = "eco"

        def get_state(entity_id: str) -> Any:
            return {
                "sensor.goodwe_soc": soc_state,
                "sensor.goodwe_house_load": loads_state,
                "select.goodwe_operation_mode": work_mode_state,
            }.get(entity_id)

        coord = _make_coordinator(
            {
                "SoC": "sensor.goodwe_soc",
                "loadsPower": "sensor.goodwe_house_load",
                "_work_mode": "select.goodwe_operation_mode",
            }
        )
        coord.hass.states.get = get_state

        data = await coord._async_update_data()
        assert data["SoC"] == 75.5
        assert data["loadsPower"] == 1.2
        assert data["_work_mode"] == "eco"
        assert data["_data_source"] == "modbus"

    @pytest.mark.asyncio
    async def test_skips_unavailable_entities(self) -> None:
        unavail_state = MagicMock()
        unavail_state.state = "unavailable"
        soc_state = MagicMock()
        soc_state.state = "50.0"

        def get_state(entity_id: str) -> Any:
            return {
                "sensor.goodwe_soc": soc_state,
                "sensor.goodwe_house_load": unavail_state,
            }.get(entity_id)

        coord = _make_coordinator(
            {
                "SoC": "sensor.goodwe_soc",
                "loadsPower": "sensor.goodwe_house_load",
            }
        )
        coord.hass.states.get = get_state

        data = await coord._async_update_data()
        assert data["SoC"] == 50.0
        assert "loadsPower" not in data
        assert data["_work_mode"] is None

    @pytest.mark.asyncio
    async def test_skips_unknown_entities(self) -> None:
        unknown_state = MagicMock()
        unknown_state.state = "unknown"
        soc_state = MagicMock()
        soc_state.state = "60.0"

        def get_state(entity_id: str) -> Any:
            return {
                "sensor.goodwe_soc": soc_state,
                "sensor.goodwe_pv": unknown_state,
            }.get(entity_id)

        coord = _make_coordinator(
            {
                "SoC": "sensor.goodwe_soc",
                "pvPower": "sensor.goodwe_pv",
            }
        )
        coord.hass.states.get = get_state

        data = await coord._async_update_data()
        assert data["SoC"] == 60.0
        assert "pvPower" not in data

    @pytest.mark.asyncio
    async def test_missing_entity_returns_none_for_work_mode(self) -> None:
        coord = _make_coordinator(
            {"_work_mode": "select.goodwe_nonexistent"}
        )
        coord.hass.states.get = MagicMock(return_value=None)

        data = await coord._async_update_data()
        assert data["_work_mode"] is None

    @pytest.mark.asyncio
    async def test_non_numeric_state_kept_as_string(self) -> None:
        """Non-numeric entity states (e.g. text sensors) preserved as strings."""
        text_state = MagicMock()
        text_state.state = "some_text_value"

        def get_state(entity_id: str) -> Any:
            return {"sensor.goodwe_text": text_state}.get(entity_id)

        coord = _make_coordinator(
            {"feedin": "sensor.goodwe_text"}
        )
        coord.hass.states.get = get_state

        data = await coord._async_update_data()
        assert data["feedin"] == "some_text_value"

    @pytest.mark.asyncio
    async def test_data_source_always_modbus(self) -> None:
        """GoodWe entity-mode always reports data_source as 'modbus'."""
        coord = _make_coordinator({})
        coord.hass.states.get = MagicMock(return_value=None)

        data = await coord._async_update_data()
        assert data["_data_source"] == "modbus"

    @pytest.mark.asyncio
    async def test_work_mode_unavailable_returns_none(self) -> None:
        unavail_state = MagicMock()
        unavail_state.state = "unavailable"

        def get_state(entity_id: str) -> Any:
            return {"select.goodwe_mode": unavail_state}.get(entity_id)

        coord = _make_coordinator(
            {"_work_mode": "select.goodwe_mode"}
        )
        coord.hass.states.get = get_state

        data = await coord._async_update_data()
        assert data["_work_mode"] is None

    @pytest.mark.asyncio
    async def test_pv_and_feedin_mapped_correctly(self) -> None:
        """Verify PV power and feed-in energy entity mappings work."""
        pv_state = MagicMock()
        pv_state.state = "3.5"
        feedin_state = MagicMock()
        feedin_state.state = "12.7"

        def get_state(entity_id: str) -> Any:
            return {
                "sensor.goodwe_pv_power": pv_state,
                "sensor.goodwe_total_export": feedin_state,
            }.get(entity_id)

        coord = _make_coordinator(
            {
                "pvPower": "sensor.goodwe_pv_power",
                "feedin": "sensor.goodwe_total_export",
            }
        )
        coord.hass.states.get = get_state

        data = await coord._async_update_data()
        assert data["pvPower"] == 3.5
        assert data["feedin"] == 12.7
