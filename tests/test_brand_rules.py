"""Brand-specific rule enforcement for GoodWe Battery Control.

These tests ensure the integration follows the shared brand contract
defined in BRAND_RULES.md.  They run as part of the normal pytest suite
and will fail CI if the integration drifts from the expected structure.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
INTEGRATION = REPO_ROOT / "custom_components" / "goodwe_battery_control"
SMART_BATTERY = INTEGRATION / "smart_battery"


# ── Rule 1: Required files ──────────────────────────────────────────


REQUIRED_FILES = [
    "__init__.py",
    "config_flow.py",
    "coordinator.py",
    "sensor.py",
    "binary_sensor.py",
    "const.py",
    "manifest.json",
    "services.yaml",
    "strings.json",
    "translations/en.json",
]


def test_required_files_exist() -> None:
    """Every brand integration must have these files."""
    missing = [f for f in REQUIRED_FILES if not (INTEGRATION / f).is_file()]
    assert not missing, f"Missing required files: {missing}"


# ── Rule 2: const.py re-exports all shared constants ────────────────


def _public_names(path: Path) -> set[str]:
    """Return top-level assigned names matching shared prefixes."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_shared_name(target.id):
                    names.add(target.id)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and _is_shared_name(node.target.id)
        ):
            names.add(node.target.id)
    return names


def _is_shared_name(name: str) -> bool:
    prefixes = ("CONF_", "DEFAULT_", "SERVICE_", "MAX_", "SMART_", "STORAGE_")
    return name.startswith(prefixes) or name == "PLATFORMS"


def _imported_names(path: Path) -> set[str]:
    """Return names imported or assigned in a module."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                real = alias.asname if alias.asname else alias.name
                if _is_shared_name(real):
                    names.add(real)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_shared_name(target.id):
                    names.add(target.id)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and _is_shared_name(node.target.id)
        ):
            names.add(node.target.id)
    return names


def test_const_reexports_shared_constants() -> None:
    """Brand const.py must re-export every constant from smart_battery/const.py."""
    shared = _public_names(SMART_BATTERY / "const.py")
    brand = _imported_names(INTEGRATION / "const.py")
    missing = shared - brand
    assert not missing, (
        f"const.py is missing re-exports for: {sorted(missing)}\n"
        "Add them as `from .smart_battery.const import X as X`"
    )


# ── Rule 3: services.yaml has the required 6 services ───────────────


REQUIRED_SERVICES = {
    "clear_overrides",
    "feedin",
    "force_charge",
    "force_discharge",
    "smart_charge",
    "smart_discharge",
}


def test_services_yaml_has_required_services() -> None:
    """services.yaml must define exactly the 6 standard services."""
    services = yaml.safe_load((INTEGRATION / "services.yaml").read_text())
    defined = set(services.keys())
    missing = REQUIRED_SERVICES - defined
    assert not missing, f"services.yaml missing required services: {sorted(missing)}"


# ── Rule 4: manifest.json structure ──────────────────────────────────


REQUIRED_MANIFEST_KEYS = {
    "domain",
    "name",
    "config_flow",
    "version",
    "codeowners",
    "documentation",
    "issue_tracker",
}


def test_manifest_structure() -> None:
    """manifest.json must have required keys and domain must match directory."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())
    missing = REQUIRED_MANIFEST_KEYS - set(manifest.keys())
    assert not missing, f"manifest.json missing keys: {sorted(missing)}"
    assert manifest["config_flow"] is True, "config_flow must be true"
    assert manifest["domain"] == INTEGRATION.name, (
        f"domain '{manifest['domain']}' != directory name '{INTEGRATION.name}'"
    )


# ── Rule 5: Sensor classes subclass shared bases ─────────────────────


def _get_base_classes(path: Path) -> dict[str, list[str]]:
    """Return {class_name: [base_class_names]} for all classes in a file."""
    tree = ast.parse(path.read_text())
    result: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases: list[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            result[node.name] = bases
    return result


def _file_imports_from(path: Path, module_fragment: str) -> set[str]:
    """Return names imported from modules containing *module_fragment*."""
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and module_fragment in node.module
        ):
            for alias in node.names:
                names.add(alias.asname if alias.asname else alias.name)
    return names


def test_sensor_classes_subclass_shared_bases() -> None:
    """All sensor classes in sensor.py must inherit from smart_battery bases."""
    shared_bases = _file_imports_from(INTEGRATION / "sensor.py", "smart_battery")
    classes = _get_base_classes(INTEGRATION / "sensor.py")
    for cls_name, bases in classes.items():
        if cls_name.startswith("_"):
            continue
        assert any(b in shared_bases for b in bases), (
            f"sensor.py: {cls_name} does not inherit from a smart_battery base. "
            f"Bases: {bases}, imported shared bases: {sorted(shared_bases)}"
        )


def test_binary_sensor_classes_subclass_shared_bases() -> None:
    """All binary_sensor classes must inherit from smart_battery bases."""
    shared_bases = _file_imports_from(INTEGRATION / "binary_sensor.py", "smart_battery")
    classes = _get_base_classes(INTEGRATION / "binary_sensor.py")
    for cls_name, bases in classes.items():
        if cls_name.startswith("_"):
            continue
        assert any(b in shared_bases for b in bases), (
            f"binary_sensor.py: {cls_name} does not inherit from a smart_battery base. "
            f"Bases: {bases}, imported shared bases: {sorted(shared_bases)}"
        )


# ── Rule 6: Coordinator subclasses shared base ──────────────────────


def test_coordinator_subclasses_shared_base() -> None:
    """coordinator.py must have a class inheriting from EntityCoordinator."""
    shared_bases = _file_imports_from(INTEGRATION / "coordinator.py", "smart_battery")
    classes = _get_base_classes(INTEGRATION / "coordinator.py")
    found = False
    for _cls_name, bases in classes.items():
        if any(b in shared_bases for b in bases):
            found = True
            break
    assert found, (
        "coordinator.py must contain a class that inherits from "
        "smart_battery EntityCoordinator"
    )


# ── Rule 7: __init__.py uses shared register_services ────────────────


def test_init_uses_shared_register_services() -> None:
    """__init__.py must import register_services from smart_battery."""
    source = (INTEGRATION / "__init__.py").read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and "smart_battery" in node.module
        ):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if name == "register_services":
                    return
    raise AssertionError(
        "__init__.py must import register_services from smart_battery.services"
    )
