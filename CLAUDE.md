# GoodWe Battery Control

## Build / Test / Lint

```bash
pytest tests/ --tb=short
pre-commit run --all-files      # ruff + mypy
```

## Key Constraints

Inherited from the shared `smart_battery/` core (foxess-control canonical source):

- **C-001**: Discharge power floored at peak_consumption x 1.5 to prevent grid import
- **C-002**: Discharge suspends at or below min SoC
- **C-003**: Session identity tokens prevent stale callback races
- **C-005**: Stale coordinator data (timeDiff > 30s) is discarded
- **C-014**: Taper profiles auto-reset if plausibility check fails (median ratio <= 0.10)
- **C-015**: Vendored smart_battery/ must be byte-identical to canonical root copy in foxess-control
- **C-017**: End-of-discharge guard: suspend when energy can't sustain safety floor for 10 min
- **C-019**: Discharge SoC unavailability aborts session after 3 checks (matching charge C-012)
- **C-024**: Safe state on failure: 3 consecutive adapter errors open circuit breaker (hold position). 5 more ticks without recovery → abort session → self-use
- **C-025**: Session boundary cleanliness: all overrides removed before new session starts
- **C-027**: Schedule end time set to safe horizon (SoC/rate/safety_factor), not full window

GoodWe-specific:

- **GW-001**: Entity-mode only — no cloud API, all control via HA select/number entities
- **GW-002**: Mode map: SELF_USE→eco, FORCE_CHARGE→eco_charge, FORCE_DISCHARGE→eco_discharge, BACKUP→backup, FEEDIN→peak_shaving
- **GW-003**: Default inverter power 5000W (ET/EH/BT/BH series)
- **GW-004**: Entity auto-detection via `goodwe` platform in HA entity registry
- **GW-005**: Supports input_select/input_number entities (not just platform-backed select/number)

## Architecture

Two-layer design: brand-agnostic `smart_battery/` core (pure pacing algorithms,
session management, sensors) + GoodWe-specific wrapper (`__init__.py`, `config_flow.py`,
`coordinator.py`). `EntityAdapter` is the control boundary — it writes mode changes
via HA `select.select_option` and `number.set_value` service calls.

Unlike foxess-control which has both cloud API and entity mode, GoodWe is entity-mode
only. The `GoodWeEntityCoordinator` polls HA entity states and returns data in the
same shape as cloud-API coordinators, so all shared algorithms work identically.

## Brand Rules

See `BRAND_RULES.md` for the integration contract enforced by CI:
- `smart_battery/` must be byte-identical to foxess-control canonical copy
- `const.py` must re-export all shared constants
- Sensors/binary sensors must subclass shared bases
- Coordinator must subclass `EntityCoordinator`
- Services registered via shared `register_services()`
