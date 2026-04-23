import os
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import config as config_module
from config.schema import InstitutionConfig


@pytest.fixture(autouse=True)
def _reset_cache():
    config_module.reset()
    yield
    config_module.reset()


def _write(path, body):
    with open(path, 'w') as f:
        f.write(body)


# --- defaults ---

def test_load_with_no_files_uses_pydantic_defaults(tmp_path):
    cfg = config_module.load(
        defaults_path=str(tmp_path / 'none.yaml'),
        user_path=str(tmp_path / 'none.yaml'),
    )
    assert isinstance(cfg, InstitutionConfig)
    assert cfg.institution.name == "Default Institution"
    assert cfg.backup.reminder_interval_days == 7
    assert 'standard_q3w' in cfg.cycles.dose_density_options


def test_load_reads_committed_defaults_yaml():
    cfg = config_module.load(user_path='/nonexistent/path.yaml')
    assert cfg.patient.id_regex == r'^PT-\d{3,}$'


# --- overrides ---

def test_user_yaml_overrides_defaults(tmp_path):
    defaults = tmp_path / 'd.yaml'
    user = tmp_path / 'u.yaml'
    _write(defaults, "institution:\n  name: Default\nbackup:\n  reminder_interval_days: 7\n")
    _write(user, "institution:\n  name: Memorial Oncology\n")
    cfg = config_module.load(defaults_path=str(defaults), user_path=str(user))
    assert cfg.institution.name == "Memorial Oncology"
    assert cfg.backup.reminder_interval_days == 7


def test_session_override_beats_user_yaml(tmp_path):
    defaults = tmp_path / 'd.yaml'
    user = tmp_path / 'u.yaml'
    _write(defaults, "backup:\n  reminder_interval_days: 7\n")
    _write(user, "backup:\n  reminder_interval_days: 14\n")
    cfg = config_module.load(
        defaults_path=str(defaults),
        user_path=str(user),
        overrides={'backup': {'reminder_interval_days': 3}},
    )
    assert cfg.backup.reminder_interval_days == 3


def test_deep_merge_preserves_unrelated_keys(tmp_path):
    defaults = tmp_path / 'd.yaml'
    user = tmp_path / 'u.yaml'
    _write(defaults, "institution:\n  name: Default\npatient:\n  id_regex: X\n")
    _write(user, "institution:\n  name: New\n")
    cfg = config_module.load(defaults_path=str(defaults), user_path=str(user))
    assert cfg.institution.name == "New"
    assert cfg.patient.id_regex == "X"


# --- validation ---

def test_invalid_backup_interval_rejected(tmp_path):
    defaults = tmp_path / 'd.yaml'
    _write(defaults, "backup:\n  reminder_interval_days: 0\n")
    with pytest.raises(ValidationError):
        config_module.load(defaults_path=str(defaults), user_path='/nope')


def test_unknown_top_level_key_rejected(tmp_path):
    defaults = tmp_path / 'd.yaml'
    _write(defaults, "unknown_section:\n  foo: bar\n")
    with pytest.raises(ValidationError):
        config_module.load(defaults_path=str(defaults), user_path='/nope')


def test_non_mapping_yaml_rejected(tmp_path):
    defaults = tmp_path / 'd.yaml'
    _write(defaults, "- just\n- a\n- list\n")
    with pytest.raises(ValueError):
        config_module.load(defaults_path=str(defaults), user_path='/nope')


def test_invalid_dose_density_option_rejected(tmp_path):
    defaults = tmp_path / 'd.yaml'
    _write(defaults, "cycles:\n  dose_density_options: [weekly]\n")
    with pytest.raises(ValidationError):
        config_module.load(defaults_path=str(defaults), user_path='/nope')


# --- get / reset ---

def test_get_returns_cached_config():
    cfg1 = config_module.load()
    cfg2 = config_module.get()
    assert cfg1 is cfg2


def test_get_lazy_loads_when_cache_empty():
    config_module.reset()
    cfg = config_module.get()
    assert cfg is not None


def test_reset_clears_cache():
    config_module.load()
    config_module.reset()
    assert config_module._active is None


# --- committed defaults file is valid ---

def test_committed_defaults_yaml_validates():
    cfg = config_module.load(user_path='/nonexistent/path.yaml')
    assert cfg.institution.name
    assert cfg.patient.id_regex
    assert cfg.backup.reminder_interval_days >= 1
