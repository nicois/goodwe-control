"""Tests for GoodWe Battery Control sensor entities.

Mirrors foxess_control test_sensor.py patterns — tests sensor display
values, icons, unique IDs, and extra state attributes.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from custom_components.goodwe_battery_control.const import (
    DEFAULT_GOODWE_INVERTER_POWER,
    DOMAIN,
)
from custom_components.goodwe_battery_control.sensor import (
    InverterOverrideStatusSensor,
)

from .conftest import charge_state, discharge_state, make_entry


def _make_hass(
    smart_charge_state: dict[str, Any] | None = None,
    smart_discharge_state: dict[str, Any] | None = None,
    coordinator_soc: float | None = None,
) -> MagicMock:
    """Create a mock hass with DOMAIN data."""
    hass = MagicMock()
    mock_coordinator = MagicMock()
    mock_coordinator.data = (
        {"SoC": coordinator_soc} if coordinator_soc is not None else None
    )
    domain_data: dict[str, Any] = {
        "_smart_charge_unsubs": [],
        "_smart_discharge_unsubs": [],
        "entry1": {"coordinator": mock_coordinator},
    }
    if smart_charge_state is not None:
        domain_data["_smart_charge_state"] = smart_charge_state
    if smart_discharge_state is not None:
        domain_data["_smart_discharge_state"] = smart_discharge_state
    hass.data = {DOMAIN: domain_data}
    return hass


class TestInverterOverrideStatusSensor:
    """Tests for the compact status sensor."""

    def test_idle(self) -> None:
        hass = _make_hass()
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Idle"
        assert sensor.icon == "mdi:home-battery"
        assert sensor.extra_state_attributes is None

    def test_charging(self) -> None:
        hass = _make_hass(smart_charge_state=charge_state())
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Chg 4kW→80%"
        assert sensor.icon == "mdi:battery-charging"

    def test_charging_fractional_power(self) -> None:
        hass = _make_hass(smart_charge_state=charge_state(last_power_w=3500))
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Chg 3.5kW→80%"

    def test_charging_low_power(self) -> None:
        hass = _make_hass(smart_charge_state=charge_state(last_power_w=500))
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Chg 500W→80%"

    def test_deferred(self) -> None:
        hass = _make_hass(
            smart_charge_state=charge_state(last_power_w=0, charging_started=False)
        )
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Wait→80%"
        assert sensor.icon == "mdi:battery-clock"

    def test_discharging(self) -> None:
        hass = _make_hass(smart_discharge_state=discharge_state())
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Dchg 3kW→20:00"
        assert sensor.icon == "mdi:battery-arrow-down"

    def test_discharging_with_feedin_limit(self) -> None:
        hass = _make_hass(
            smart_discharge_state=discharge_state(feedin_energy_limit_kwh=5.0)
        )
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Dchg 3kW 5.0kWh"

    def test_charge_priority(self) -> None:
        """If both states exist, charge takes priority."""
        hass = _make_hass(
            smart_charge_state=charge_state(),
            smart_discharge_state=discharge_state(),
        )
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        assert sensor.native_value == "Chg 4kW→80%"

    def test_unique_id(self) -> None:
        sensor = InverterOverrideStatusSensor(_make_hass(), make_entry("abc"))
        assert sensor.unique_id == "abc_override_status"

    def test_translation_key(self) -> None:
        sensor = InverterOverrideStatusSensor(_make_hass(), make_entry())
        assert sensor.translation_key == "override_status"

    def test_attributes_charging(self) -> None:
        hass = _make_hass(smart_charge_state=charge_state())
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["mode"] == "smart_charge"
        assert attrs["phase"] == "charging"
        assert attrs["power_w"] == 4000
        assert attrs["max_power_w"] == DEFAULT_GOODWE_INVERTER_POWER
        assert attrs["target_soc"] == 80
        assert attrs["end_time"] == "2026-04-08T06:00:00"

    def test_attributes_discharging(self) -> None:
        hass = _make_hass(smart_discharge_state=discharge_state())
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["mode"] == "smart_discharge"
        assert attrs["power_w"] == 3000
        assert attrs["min_soc"] == 30
        assert attrs["end_time"] == "2026-04-08T20:00:00"

    def test_attributes_deferred(self) -> None:
        hass = _make_hass(
            smart_charge_state=charge_state(last_power_w=0, charging_started=False)
        )
        sensor = InverterOverrideStatusSensor(hass, make_entry())
        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["mode"] == "smart_charge"
        assert attrs["phase"] == "deferred"
