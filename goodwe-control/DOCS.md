# GoodWe Battery Control

A Home Assistant custom integration for smart battery charge/discharge management on GoodWe inverters via local entity control.

## What this add-on does

This add-on installs the GoodWe Battery Control integration into your Home Assistant instance. On startup it copies the integration files into your `custom_components/` directory. You must restart Home Assistant after the first install for the integration to load.

## Installation

1. Add this repository to your Home Assistant add-on store:
   **Settings > Add-ons > Add-on Store > ⋮ > Repositories** and enter `https://github.com/nicois/goodwe-control`.
2. Install **GoodWe Battery Control** from the store.
3. Start the add-on.
4. Restart Home Assistant.

## After installation

Once Home Assistant restarts, configure the integration:

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **GoodWe Battery Control**.
3. Select your GoodWe inverter entities (work mode, charge/discharge power, SoC, etc.).

For full documentation on configuration options, actions, and features, see the [README](https://github.com/nicois/goodwe-control).

## Updating

When a new version is available, update the add-on in the add-on store and restart Home Assistant.
