## 1.0.2-beta.1

### Changed
- Synced `smart_battery/` with foxess-control v1.0.7-beta.15
- Two-tier circuit breaker: 3 consecutive adapter errors open circuit breaker (hold position), 5 more ticks without recovery abort session to self-use (C-024)
- Safe schedule end time: discharge horizon set to SoC/rate/safety_factor, not full window (C-027)
- Session state restoration across HA restarts via typed domain data
- Improved error surfacing and session logging with structured context filter
- Aligned CI workflows with foxess-control (actions v6, gate-based release)

## 1.0.1-beta.4

### Added
- **Peak consumption tracking with safety floor**: tracks highest observed consumption with exponential decay (~21 min half-life), floors discharge power at peak × 1.5 to prevent grid import from inter-poll load spikes
- **Priority-weighted discharge**: strict P1 no-import > P2 min-SoC > P3 energy-target > P4 maximise-feed-in ordering with peak-aware deferred start and suspension

## 1.0.1-beta.3

### Added
- **Deferred self-use for smart discharge**: stays in self-use mode as long as possible, then switches to forced discharge only when a calculated deadline requires it — prevents accidental grid import when paced discharge power would be below house load

### Fixed
- **Discharge power floor at house consumption**: during forced discharge, power is now floored at house load to prevent grid import

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
