## 1.0.1

### Added
- **End-of-discharge guard (C-017)**: suspend discharge when remaining energy can't sustain the safety floor for 10 minutes
- **Peak consumption tracking with safety floor**: tracks highest observed consumption with exponential decay (~21 min half-life), floors discharge power at peak x 1.5 to prevent grid import from inter-poll load spikes
- **Priority-weighted discharge**: strict P1 no-import > P2 min-SoC > P3 energy-target > P4 maximise-feed-in ordering with peak-aware deferred start and suspension
- **Deferred self-use for smart discharge**: stays in self-use mode as long as possible, then switches to forced discharge only when a calculated deadline requires it
- **SoC interpolation**: sub-percent SoC estimates between integer ticks for smoother progress display
- **Two-zone SoC progress bar**: solid confirmed + semi-transparent projected zone on charge/discharge bars
- **Schedule horizon marker**: time progress bar shows how far ahead the inverter schedule extends
- **Safe schedule end time (C-027)**: schedule end set to SoC/rate/safety_factor horizon, not full window
- **Discharge SoC unavailability abort (C-019)**: discharge sessions abort after 3 consecutive SoC-unavailable checks, matching charge path behaviour
- **Safe state on failure (C-024)**: listener callbacks catch unexpected exceptions, cancel the session, and revert to self-use
- **Unreachable charge target detection (C-022)**: new `charge_target_reachable` attribute on the smart operations sensor
- **Proactive error surfacing (C-026)**: session errors surfaced via sensor attributes (`has_error`, `last_error`, `last_error_at`, `error_count`)
- **Session cancel hook**: brand-specific post-cancel callback
- **Entity adapter input_select/input_number support (GW-005)**: service domain derived from entity prefix
- **Power progress bars with expandable tooltips** on Lovelace card
- **Test suite**: adapter, coordinator, service, and sensor tests mirroring foxess-control entity-mode test patterns

### Fixed
- **Discharge power floor at house consumption**: during forced discharge, power is now floored at house load to prevent grid import
- **Taper-path consumption bypass (D-007)**: deferred start taper paths now account for household consumption
- **Taper save interval aligned (D-012)**: charge and discharge both use `_TAPER_SAVE_EVERY_N=5`

### Changed
- Min SoC floor lowered from 5% to 0% in config flow and discharge service schema
- Progress bars hidden when charge is deferred or discharge is pre-scheduled
- Overview card retries entity map discovery after reload (10s cooldown)
- House node shown as active when consuming 0W (not dimmed)
- Synced smart_battery core from foxess-control v1.0.1-beta.29

## 1.0.0

### Added
- **Smart charge**: pace charging to reach a target SoC by a deadline, deferring grid charging to maximise solar contribution
- **Smart discharge**: pace discharging with min-SoC protection, consumption-aware power adjustment, and optional feed-in energy limits
- **Force charge / discharge / feed-in**: immediate overrides with auto-revert
- **Entity mode**: controls via existing GoodWe HA entities (no cloud API needed)
- **Session persistence**: smart sessions survive HA restarts
- **Lovelace cards**: control card (`custom:goodwe-control-card`) and overview card (`custom:goodwe-overview-card`) with auto-discovery via WebSocket entity map
- **Full i18n support** (10 languages): English, German, French, Dutch, Spanish, Italian, Polish, Portuguese, Simplified Chinese, Japanese — entity names, service descriptions, config UI, and card labels
- **Adaptive BMS taper model**: learns actual charge/discharge acceptance at each SoC level, improving time estimates and power pacing at high/low SoC
- **Brand rule enforcement**: CI validates shared `smart_battery/` library stays in sync with the canonical source in foxess-control
