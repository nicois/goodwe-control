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
