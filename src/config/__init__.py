"""Institutional configuration loader.

Resolution order: hard-coded Pydantic defaults → defaults YAML → user YAML
→ session overrides. load() is called once at startup; get() returns the
active InstitutionConfig.
"""

import os
from typing import Any, Optional

import yaml

from .schema import InstitutionConfig

_CONFIG_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'config')
)
DEFAULTS_PATH = os.path.join(_CONFIG_DIR, 'institution.defaults.yaml')
USER_PATH = os.path.join(_CONFIG_DIR, 'institution.yaml')

_active: Optional[InstitutionConfig] = None


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively; override wins on leaves."""
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _read_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def load(
    defaults_path: str = DEFAULTS_PATH,
    user_path: str = USER_PATH,
    overrides: Optional[dict] = None,
) -> InstitutionConfig:
    """Load config from disk and cache it. Returns the active InstitutionConfig."""
    global _active
    merged: dict = {}
    merged = _deep_merge(merged, _read_yaml(defaults_path))
    merged = _deep_merge(merged, _read_yaml(user_path))
    if overrides:
        merged = _deep_merge(merged, overrides)
    _active = InstitutionConfig(**merged)
    return _active


def get() -> InstitutionConfig:
    """Return the active config, loading from defaults if not yet initialized."""
    if _active is None:
        return load()
    return _active


def reset() -> None:
    """Drop the cached config. Used by tests."""
    global _active
    _active = None
