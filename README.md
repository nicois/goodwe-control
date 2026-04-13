# GoodWe Battery Control

Smart battery control for GoodWe inverters via Home Assistant.

Uses the [smart_battery](https://github.com/nicois/foxess-control) shared
library to provide intelligent charge/discharge pacing, deferred start,
consumption-aware suspension, and feed-in budget management.

## Installation

Install via [HACS](https://hacs.xyz/) by adding this repository as a custom
integration repository.

## Features

- **Smart Charge** — pace charging to reach a target SoC by a deadline
- **Smart Discharge** — pace discharging with min-SoC protection and feed-in limits
- **Force Charge / Discharge** — immediate override with auto-revert
- **Feed-in** — prioritise grid export for a set duration
- **Entity mode** — controls via existing GoodWe HA entities (no cloud API needed)

## Configuration

After installation, add the integration via **Settings → Devices & Services → Add Integration → GoodWe Battery Control**.

The options flow will auto-detect GoodWe entities from your existing HA setup
and let you configure battery capacity, min SoC, and other parameters.

## Brand Rules

This integration vendors a shared `smart_battery/` library from
[foxess-control](https://github.com/nicois/foxess-control). CI enforces
byte-for-byte identity of the shared code. See [BRAND_RULES.md](BRAND_RULES.md)
for the full contract.
