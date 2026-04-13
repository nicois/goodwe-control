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
