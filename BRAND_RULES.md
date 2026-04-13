# Brand Integration Rules

This document defines the contract between a brand-specific integration
(e.g. `goodwe_battery_control`) and the shared `smart_battery/` library
vendored from the canonical source in
[foxess-control](https://github.com/nicois/foxess-control).

All rules are enforced by CI (see `tests/test_brand_rules.py` and
`.github/workflows/drift.yml`).

---

## MUST be identical

| What | Enforcement |
|---|---|
| `smart_battery/` directory | `drift.yml` — byte-for-byte comparison against canonical source in foxess-control |

To sync: `scripts/sync_smart_battery.sh`

---

## MUST follow pattern

| Rule | File(s) | Enforcement |
|---|---|---|
| Re-export all shared `CONF_*`, `DEFAULT_*`, `SERVICE_*`, `PLATFORMS` constants | `const.py` | `test_const_reexports_shared_constants` |
| Define the 6 standard services | `services.yaml` | `test_services_yaml_has_required_services` |
| All sensor classes subclass `smart_battery.sensor_base` bases | `sensor.py`, `binary_sensor.py` | `test_sensor_classes_subclass_shared_bases`, `test_binary_sensor_classes_subclass_shared_bases` |
| Coordinator subclasses `smart_battery.coordinator.EntityCoordinator` | `coordinator.py` | `test_coordinator_subclasses_shared_base` |
| Import and call `register_services()` from shared code | `__init__.py` | `test_init_uses_shared_register_services` |
| Required files present | all | `test_required_files_exist` |
| `manifest.json` has required keys; `domain` matches directory name | `manifest.json` | `test_manifest_structure` |

---

## MAY differ (brand-specific)

| What | Examples |
|---|---|
| `const.py` | `DOMAIN`, `DEFAULT_*_INVERTER_POWER`, brand-specific constants |
| `__init__.py` | Mode map (e.g. `_GOODWE_MODE_MAP`), storage key, adapter config |
| `config_flow.py` | Entity name mapping, auto-detection logic, credential steps (cloud API brands) |
| `sensor.py` / `binary_sensor.py` | `_device_info()` (manufacturer, model), additional brand-specific sensors |
| `manifest.json` | `domain`, `name`, `iot_class`, `version`, brand-specific `requirements` |
| `strings.json` / `translations/` | Brand-specific UI text |
| `services.yaml` | Additional fields per service (e.g. `replace_conflicts` for cloud-only brands) |

---

## Adding a new brand

1. Fork this repo as a template
2. Replace all `goodwe` / `GoodWe` references with your brand name
3. Define `DOMAIN` and mode mapping in `const.py` / `__init__.py`
4. Write entity detection in `config_flow.py` for the brand's HA integration
5. Run `scripts/sync_smart_battery.sh` to get the latest shared code
6. Run `pytest` — all brand rules must pass
7. Register on HACS
