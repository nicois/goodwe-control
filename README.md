# GoodWe Battery Control

A Home Assistant custom integration for controlling GoodWe inverter battery modes.

GoodWe Battery Control provides actions for force charge, force discharge, smart charge/discharge with SoC targets, and feed-in management. It controls the inverter via **entity mode** — reading state from and writing mode changes to existing GoodWe HA entities (e.g. from [home-assistant-goodwe-inverter](https://github.com/mletenay/home-assistant-goodwe-inverter)). No cloud API connection is required.

## Gallery
### Smart charge: optimally ensure SoC is reached at a given time
<img width="481" height="746" alt="image" src="https://github.com/user-attachments/assets/998b4aec-d923-4188-b669-28b56fccf73a" />

### Smart discharge: feed in during a time window, optionally limiting total energy, reverting to self-use afterwards. If minimum SoC will be reached, throttle discharge rate to not reach it prematurely
<img width="481" height="873" alt="image" src="https://github.com/user-attachments/assets/1272ba4a-111f-45d4-a53e-6a3e7918efc9" />

### A dashboard card showing the state of the current smart operation
<img width="517" height="313" alt="image" src="https://github.com/user-attachments/assets/713e2a6e-9f57-42fa-bc9a-bf1344acb16a" />



## Prerequisites

- A GoodWe inverter with a compatible Home Assistant integration providing entities for work mode, charge/discharge power, and SoC (e.g. [home-assistant-goodwe-inverter](https://github.com/mletenay/home-assistant-goodwe-inverter))

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations**.
3. Click the three-dot menu in the top right and select **Custom repositories**.
4. Add the repository URL (e.g. `https://github.com/nicois/goodwe-control`) with category **Integration**.
5. Click **Add**.
6. Search for "GoodWe Battery Control" in the HACS integrations list and click **Download**.
7. Restart Home Assistant.

### Manual

1. Copy the `custom_components/goodwe_battery_control` directory into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **GoodWe Battery Control**.
3. The integration is added immediately (no credentials required — all control is via local entities).

### Options

After setup, click **Configure** on the integration entry to adjust:

| Option | Default | Range | Description |
|---|---|---|---|
| Minimum SoC on Grid | 15% | 5-100% | The minimum battery state of charge to maintain when on grid. Applied to all schedule operations. |
| Polling Interval | 30 s | 60-600 s | How often to poll entity states for real-time data. Defaults to 30 seconds since reads are local. |
| Battery Capacity | 0.0 kWh | 0-100 kWh | Total usable battery capacity in kWh. Required for `smart_charge` power calculations. |
| Min Power Change | 500 W | 0-5000 W | Minimum watt change before updating the charge power during `smart_charge`. Lower values improve SoC tracking, higher values reduce entity writes. |
| Minimum API fdSoc | 11% | 0-11% | The minimum `fdSoc` value used internally. Only lower this if you know your inverter supports it. |
| Smart Headroom | 10% | 0-25% | Spare capacity reserved during `smart_charge` and `smart_discharge` for transient load variation. Applied as both a time buffer (plan to finish in 90% of the window) and a power multiplier (request 110% of the calculated rate). For smart charge, lower values charge more slowly and defer longer; higher values start earlier and charge faster. For smart discharge, the headroom ensures the battery is not drained too quickly, reaching `min_soc` near the end of the window. Set to 0 for no headroom (not recommended — transient loads may prevent reaching the target). |

### Entity mapping

The options flow automatically shows an entity mapping step. Entities are **auto-detected** from the GoodWe entity registry and pre-populated — in most cases no manual configuration is needed. You can override any mapping if the auto-detection picks the wrong entity.

| Option | Domain | Required | Description |
|---|---|---|---|
| Work Mode Entity | `select` | Yes | GoodWe work mode select entity. |
| Charge Power Entity | `number` | For smart charge | GoodWe charge power number entity. |
| Discharge Power Entity | `number` | For smart discharge | GoodWe discharge power number entity. |
| Min SoC Entity | `number` | No | GoodWe min SoC number entity. |
| SoC Entity | `sensor` | No | Battery SoC sensor. |
| Loads Power Entity | `sensor` | No | House load sensor (improves consumption-aware charging). |
| PV Power Entity | `sensor` | No | Solar generation sensor (improves charge deferral). |
| Feed-in Energy Entity | `sensor` | No | Cumulative feed-in energy sensor (for discharge energy limits). |
| Inverter Rated Power | — | No | Inverter's maximum power in watts (default 5000). Used as the default power limit when no explicit power is specified in actions. |

How entity mode works:

- **No cloud connection required.** All control is via local HA entities.
- **Reads** come from HA entity states (polled every 30 seconds by default).
- **Writes** use `select.select_option` and `number.set_value` service calls to GoodWe entities.
- All actions (`force_charge`, `smart_charge`, `smart_discharge`, `feedin`, `clear_overrides`) work identically to other smart battery integrations — only the underlying transport changes.
- Schedule merging and multi-window management are not used; the integration sets the mode directly.
- Smart session recovery after HA restart works without checking cloud schedule state.

## Actions

The integration registers six actions (services) under the `goodwe_battery_control` domain. These are intended to be called from automations.

### `goodwe_battery_control.clear_overrides`

Clears overrides and returns the inverter to self-use mode. If `mode` is specified, only overrides of that mode are removed; other overrides are retained.

If a `smart_charge` or `smart_discharge` session is running, `clear_overrides` also cancels its background listeners — the session stops cleanly without fighting the cleared schedule. Clearing `ForceCharge` cancels smart charge; clearing `ForceDischarge` cancels smart discharge; clearing all overrides (no `mode`) cancels both.

| Parameter | Required | Default | Description |
|---|---|---|---|
| `mode` | No | All | Only clear overrides of this mode (`ForceCharge`, `ForceDischarge`, etc.). |

```yaml
# Clear all overrides (also stops any active smart charge/discharge)
action: goodwe_battery_control.clear_overrides
```

```yaml
# Clear only force-charge overrides (also stops smart charge), keeping others
action: goodwe_battery_control.clear_overrides
data:
  mode: ForceCharge
```

### `goodwe_battery_control.feedin`

Prioritises feeding excess solar to the grid for a specified duration, similar to self-use but with grid export priority. The inverter automatically reverts to self-use when the window ends. Does not cancel running smart charge/discharge sessions.

| Parameter | Required | Default | Description |
|---|---|---|---|
| `duration` | Yes | | How long to feed in. Maximum 4 hours. Must not extend past midnight. |
| `power` | No | Inverter max | Feed-in power limit in watts (min 100). |
| `start_time` | No | Now | Time of day to start the override (e.g. `"14:00:00"`). |

```yaml
action: goodwe_battery_control.feedin
data:
  duration: "02:00:00"
  power: 5000
```

### `goodwe_battery_control.force_charge`

Forces the inverter to charge the battery for a specified duration. The inverter automatically reverts to self-use when the window ends. Cancels any running `smart_charge` session, since it replaces the underlying `ForceCharge` schedule.

| Parameter | Required | Default | Description |
|---|---|---|---|
| `duration` | Yes | | How long to force charge. Maximum 4 hours. Must not extend past midnight. |
| `power` | No | Inverter max | Charge power limit in watts (min 100). |
| `start_time` | No | Now | Time of day to start the override (e.g. `"14:30:00"`). |

```yaml
action: goodwe_battery_control.force_charge
data:
  duration: "01:30:00"
  power: 5000
```

### `goodwe_battery_control.force_discharge`

Forces the inverter to discharge the battery for a specified duration. The inverter automatically reverts to self-use when the window ends. Cancels any running `smart_discharge` session, since it replaces the underlying `ForceDischarge` schedule.

| Parameter | Required | Default | Description |
|---|---|---|---|
| `duration` | Yes | | How long to force discharge. Maximum 4 hours. Must not extend past midnight. |
| `power` | No | Inverter max | Discharge power limit in watts (min 100). |
| `start_time` | No | Now | Time of day to start the override (e.g. `"17:00:00"`). |

```yaml
action: goodwe_battery_control.force_discharge
data:
  duration: "02:00:00"
  power: 5000
```

### `goodwe_battery_control.smart_charge`

Charges the battery within a time window, deferring grid charging as long as possible to maximise the opportunity for solar to contribute. Only starts grid charging when necessary to reach the target SoC by the end of the window.

**How it works:**

1. Calculates the latest possible start time by estimating the effective charge rate — inverter max power minus current household consumption (read from the polled `loadsPower` and `pvPower` data), with a minimum headroom (configurable via **Smart Headroom**, default 10%) reserved for transient loads. This consumption-aware calculation means the deferral adapts to real-time site conditions rather than using a fixed buffer.
2. **Deferred phase:** Until the calculated start time, no `ForceCharge` override is set. The inverter stays in its current mode (typically self-use), allowing solar generation to charge the battery naturally.
3. **Charging phase:** When the deferred start time arrives, sets the inverter to `ForceCharge` mode. Charge power targets finishing within the configured headroom buffer and accounts for current household consumption, so the inverter typically runs below full capacity.
4. Every 5 minutes, re-reads the current SoC, household consumption, and solar generation, then recalculates. During the deferred phase, if solar has raised the SoC, the start time is pushed later. During the charging phase, power is adjusted up or down based on both the remaining energy deficit and current net consumption. If the power change is below the configured **Min Power Change** threshold, the update is skipped to avoid unnecessary entity writes. If the actual energy stored is significantly behind the ideal headroom-adjusted trajectory (a linear ramp from the starting energy to the target, completing within the headroom-shortened window), the charge rate temporarily jumps to full power until the trajectory is regained. The deficit must exceed a tolerance derived from the **Min Power Change** setting to avoid premature bursting from minor measurement fluctuations.
5. When the SoC reaches the target (whether from solar during the deferred phase or grid charging), the `ForceCharge` override is removed immediately to stop unnecessary charging. The session continues monitoring for one more reading: if the SoC is confirmed at or above target, the session ends; if it drops back below, the charge override is re-applied. This prevents a single SoC spike from prematurely ending the session while avoiding overcharging during the confirmation period.
6. When the time window ends, the override is removed and listeners are cancelled.

If the battery capacity is too large or the SoC too low to reach the target within the window (accounting for current consumption), charging starts immediately (no deferral).

Only one smart charge session can be active at a time. Starting a new `smart_charge` cancels any previous session, and also cancels any active `smart_discharge` session to prevent conflicts. A `force_charge` action also cancels any running smart charge, since it replaces the underlying `ForceCharge` mode.

**Stopping a running smart charge:** Call `goodwe_battery_control.clear_overrides` (with no mode, or with `mode: ForceCharge`). This removes the override **and** cancels the background listeners.

**HA restart:** Smart charge sessions are persisted to `.storage`. If HA restarts mid-session, the session is automatically resumed if still within the time window, or cleaned up if expired. You do not need to re-trigger the automation.

**Requires** Battery Capacity to be configured in the integration options.

| Parameter | Required | Default | Description |
|---|---|---|---|
| `start_time` | Yes | | Time of day to start charging (e.g. `"02:00:00"`). |
| `end_time` | Yes | | Time of day to stop charging (e.g. `"06:00:00"`). Must be after start time, within 4 hours. |
| `target_soc` | Yes | | Charge the battery to this SoC level (5-100%). Charging stops and reverts to self-use when reached. |
| `power` | No | Inverter max | Maximum charge power in watts (min 100). The actual power may be lower to pace charging to the end of the window. |

```yaml
action: goodwe_battery_control.smart_charge
data:
  start_time: "02:00:00"
  end_time: "06:00:00"
  target_soc: 80
  power: 5000
```

### `goodwe_battery_control.smart_discharge`

Discharges the battery within a time window and automatically reverts to self-use when the battery reaches a minimum SoC. This replaces the need for a separate automation to monitor SoC and cancel the discharge.

**How it works:**

1. Sets the inverter to `ForceDischarge` mode.
2. **Power pacing** (requires `battery_capacity_kwh` in options): Calculates the discharge rate needed to reach `min_soc` by the end of the window, accounting for household consumption (which assists discharge) and applying the configurable Smart Headroom buffer. When `feedin_energy_limit_kwh` is set, pacing factors in the remaining export budget: the target energy is capped so the export is spread evenly across the window, preventing the session from exhausting the feed-in limit early and stopping before `min_soc` is reached. The power is recalculated every 5 minutes and adjusted if the change exceeds the Minimum Power Change threshold. Without `battery_capacity_kwh` configured, the discharge runs at the inverter's maximum power (or the user-specified `power` limit). When a `power` value is provided, it acts as a ceiling — pacing still operates but never exceeds the specified limit.
3. Monitors the battery SoC periodically. When the SoC drops to the `min_soc` threshold for two consecutive readings, the `ForceDischarge` override is removed, all listeners are cancelled, and the session ends. Requiring two readings prevents a single SoC dip from prematurely ending the session.
4. If `feedin_energy_limit_kwh` is set, the cumulative grid feed-in counter is snapshot at the start and compared each interval. When the exported energy reaches the limit, the session ends. This uses the lifetime `feedin` counter rather than integrating instantaneous power, so it is accurate across HA restarts.
5. When the time window ends, the override is removed and listeners are cancelled.

The session stops at whichever condition is reached first: time window end, SoC threshold, or feed-in energy limit.

Only one smart discharge session can be active at a time. Starting a new `smart_discharge` cancels any previous session, and also cancels any active `smart_charge` session to prevent conflicts. A `force_discharge` action also cancels any running smart discharge, since it replaces the underlying `ForceDischarge` mode.

**Stopping a running smart discharge:** Call `goodwe_battery_control.clear_overrides` (with no mode, or with `mode: ForceDischarge`). This removes the override **and** cancels the background listeners.

**HA restart:** Smart discharge sessions are persisted to `.storage`. If HA restarts mid-session, the session is automatically resumed if still within the time window, or cleaned up if expired.

Battery SoC is read from the integration's polled entity data.

| Parameter | Required | Default | Description |
|---|---|---|---|
| `start_time` | Yes | | Time of day to start discharging (e.g. `"17:00:00"`). |
| `end_time` | Yes | | Time of day to stop discharging (e.g. `"20:00:00"`). Must be after start time, within 4 hours. |
| `power` | No | Inverter max | Discharge power limit in watts (min 100). |
| `min_soc` | Yes | | Stop discharging and revert to self-use when the battery reaches this SoC level (5-100%). |
| `feedin_energy_limit_kwh` | No | | Stop discharging after this much energy (kWh) has been fed into the grid. This is the excess energy exported beyond household self-consumption. Uses the cumulative `feedin` counter for accuracy across restarts. |

```yaml
action: goodwe_battery_control.smart_discharge
data:
  start_time: "17:00:00"
  end_time: "20:00:00"
  min_soc: 30
  power: 5000
```

```yaml
# Discharge up to 5 kWh of grid feed-in, then stop
action: goodwe_battery_control.smart_discharge
data:
  start_time: "17:00:00"
  end_time: "20:00:00"
  min_soc: 10
  feedin_energy_limit_kwh: 5.0
```

## Sensors

### Smart operation sensors

The following sensors track active smart charge/discharge sessions. They are unavailable when no smart operation is active.

#### Overview sensors

| Entity | Description | Example value |
|---|---|---|
| `sensor.goodwe_status` | Compact status for Android Auto. Dynamic icon reflects current state. | `Chg 5kW→80%`, `Wait→80%`, `Dchg@18:00`, `Dchg 5kW→20:00`, `Dchg 5kW 5.0kWh`, `Idle` |
| `sensor.goodwe_smart_operations` | Dashboard overview with rich attributes for templating (see below). | `Charging to 80%`, `Deferred charge to 80%`, `Discharge scheduled at 18:00`, `Discharging until 20:00`, `Discharging 5.0 kWh feed-in`, `Idle` |

**`sensor.goodwe_smart_operations` attributes:**

Always present:

| Attribute | Type | Description |
|---|---|---|
| `charge_active` | bool | Whether a smart charge session is running. |
| `discharge_active` | bool | Whether a smart discharge session is running. |

When `charge_active` is true:

| Attribute | Type | Description |
|---|---|---|
| `charge_phase` | string | `"charging"` or `"deferred"`. |
| `charge_power_w` | int | Current charge power in watts. |
| `charge_max_power_w` | int | Configured maximum charge power. |
| `charge_target_soc` | int | Target SoC percentage. |
| `charge_current_soc` | float | Current battery SoC. |
| `charge_window` | string | Time window (e.g. `"02:00 – 06:00"`). |
| `charge_remaining` | string | Time remaining or deferred status (e.g. `"1h 30m"`, `"starts in 2h 15m"`). |
| `charge_end_time` | string | End time in ISO format. |

When `discharge_active` is true:

| Attribute | Type | Description |
|---|---|---|
| `discharge_power_w` | int | Current discharge power in watts. |
| `discharge_min_soc` | int | Minimum SoC threshold. |
| `discharge_current_soc` | float | Current battery SoC. |
| `discharge_window` | string | Time window (e.g. `"17:00 – 20:00"`). |
| `discharge_remaining` | string | Time remaining or status (e.g. `"45m"`, `"1.0 kWh left"`). |
| `discharge_end_time` | string | End time in ISO format. |

#### Smart charge sensors

| Entity | Description | Example value |
|---|---|---|
| `sensor.goodwe_charge_power` | Current charge power in watts. | `5000` |
| `sensor.goodwe_charge_window` | Charge time window. | `02:00 – 06:00` |
| `sensor.goodwe_charge_remaining` | Time remaining in the charge window, or time until deferred charging begins. | `1h 30m`, `starts in 2h 15m`, `starting` |

#### Smart discharge sensors

| Entity | Description | Example value |
|---|---|---|
| `sensor.goodwe_discharge_power` | Current discharge power in watts. | `5000` |
| `sensor.goodwe_discharge_window` | Discharge time window. | `17:00 – 20:00` |
| `sensor.goodwe_discharge_remaining` | Time remaining in the discharge window, energy remaining if energy limit is closer, or time until discharge begins. | `45m`, `1h 20m`, `1.0 kWh left`, `starts in 3h 45m` |

#### Battery forecast sensor

| Entity | Description |
|---|---|
| `sensor.goodwe_battery_forecast` | Projected battery SoC (%) over time. The `forecast` attribute contains a list of `{"time": <epoch_ms>, "soc": <float>}` data points (5-minute intervals) for charting. |

The forecast projects SoC based on the active smart operation:
- **Charging**: SoC rises from current level toward target_soc at the current charge power
- **Deferred charge**: SoC stays flat until the estimated start time, then rises
- **Discharging**: SoC drops from current level toward min_soc at the current discharge power

Requires **Battery Capacity** to be configured in the integration options.

#### ApexCharts example

Use the [apexcharts-card](https://github.com/RomRider/apexcharts-card) custom card to display the forecast on a dashboard:

```yaml
type: custom:apexcharts-card
header:
  title: Battery Forecast
  show: true
graph_span: 6h
yaxis:
  - min: 0
    max: 100
    decimals: 0
    apex_config:
      title:
        text: "SoC %"
series:
  - entity: sensor.goodwe_battery_forecast
    data_generator: |
      return entity.attributes.forecast.map(p => [p.time, p.soc]);
    name: Forecast
    type: area
    color: "#4CAF50"
    opacity: 0.3
    stroke_width: 2
```

To overlay the forecast on top of actual SoC history:

```yaml
type: custom:apexcharts-card
header:
  title: Battery SoC
  show: true
graph_span: 12h
span:
  start: day
yaxis:
  - min: 0
    max: 100
    decimals: 0
series:
  - entity: sensor.goodwe_battery_soc
    name: Actual
    type: area
    color: "#2196F3"
    opacity: 0.2
    stroke_width: 2
  - entity: sensor.goodwe_battery_forecast
    data_generator: |
      return entity.attributes.forecast.map(p => [p.time, p.soc]);
    name: Forecast
    type: line
    color: "#FF9800"
    stroke_width: 2
    stroke_dash: 4
```

## Binary sensors

The integration creates two binary sensors that track whether a smart charge or smart discharge session is currently active:

| Entity | State | Attributes when on |
|---|---|---|
| `binary_sensor.goodwe_smart_charge_active` | `on` while a smart charge session is running | `target_soc`, `current_power_w`, `max_power_w`, `end_time` |
| `binary_sensor.goodwe_smart_discharge_active` | `on` while a smart discharge session is running | `min_soc`, `last_power_w`, `end_time` |

These sensors are useful for:
- Dashboard indicators showing active sessions
- Automation conditions (e.g. suppress other actions while a smart charge is in progress)
- Template sensors that expose session attributes like remaining time or current power

## Automation examples

Smart charge during off-peak hours to 80%, then smart discharge during the evening peak down to 30%:

```yaml
automation:
  - alias: "Off-peak smart charge"
    trigger:
      - platform: time
        at: "02:00:00"
    action:
      - action: goodwe_battery_control.smart_charge
        data:
          start_time: "02:00:00"
          end_time: "06:00:00"
          target_soc: 80

  - alias: "Evening peak smart discharge"
    trigger:
      - platform: time
        at: "17:00:00"
    action:
      - action: goodwe_battery_control.smart_discharge
        data:
          start_time: "17:00:00"
          end_time: "20:00:00"
          min_soc: 30
```

## How it works

- Force charge/discharge actions set the inverter's work mode directly via GoodWe entity service calls. The integration manages time windows using Home Assistant timers — no cloud schedule involved.
- There is no multi-window schedule management. Each action sets a single mode; `clear_overrides` returns to self-use (eco mode).
- Smart sessions use the same algorithms (consumption-aware deferral, SoC monitoring, power adjustment) as other smart battery integrations — only the underlying transport differs.
- Session recovery after HA restart resumes based on persisted state without needing to verify cloud schedule groups.

## Known limitations

- **Minimum SoC behaviour is unintuitive**: When the battery reaches the minimum SoC during force discharge or feed-in, the inverter's behaviour may not match expectations. Smart actions work around this by monitoring SoC directly and stopping the action at the user's configured target. For plain `force_charge`/`force_discharge`, consider using an automation to cancel the override before the battery reaches the minimum SoC level.

## Brand rules

This integration vendors a shared `smart_battery/` library from [foxess-control](https://github.com/nicois/foxess-control). CI enforces byte-for-byte identity of the shared code. See [BRAND_RULES.md](BRAND_RULES.md) for the full contract.

## Support

If you find this integration useful, consider buying me a coffee:

[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?hosted_button_id=3NEP4LZAHLH6W)

## License

MIT
