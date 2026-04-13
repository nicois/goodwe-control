## 1.0.0-beta.13

### Added
- **Lovelace cards**: control card (`custom:goodwe-control-card`) and overview card (`custom:goodwe-overview-card`) with auto-discovery via WebSocket entity map
- **Full i18n support** (10 languages): English, German, French, Dutch, Spanish, Italian, Polish, Portuguese, Simplified Chinese, Japanese — entity names, service descriptions, config UI, and card labels
- **Adaptive BMS taper model**: learns actual charge/discharge acceptance at each SoC level, improving time estimates and power pacing at high/low SoC

### Changed
- Smart charge/discharge service descriptions now accurately describe rate pacing and deferred start behaviour
- Synced smart_battery library with canonical source (enum state keys, taper formatting)

## 1.0.0-beta.6

- Fix pre-commit CI (ruff lint, mypy types-PyYAML)
- Add CHANGELOG, README, brand icon for HACS validation

## 1.0.0-beta.5

Initial release of GoodWe Battery Control — smart battery management for
GoodWe inverters via Home Assistant entity mode.

- **Smart charge**: pace charging to reach a target SoC by a deadline, deferring
  grid charging to maximise solar contribution
- **Smart discharge**: pace discharging with min-SoC protection, consumption-aware
  power adjustment, and optional feed-in energy limits
- **Force charge / discharge / feed-in**: immediate overrides with auto-revert
- **Entity mode**: controls via existing GoodWe HA entities (no cloud API needed)
- **Session persistence**: smart sessions survive HA restarts
- **Brand rule enforcement**: CI validates shared `smart_battery/` library stays
  in sync with the canonical source in foxess-control
