"""Effective configuration: DEFAULTS plus per-customer overrides."""
import copy

from .defaults import DEFAULTS


def load(overrides=None):
    """Return DEFAULTS updated by `overrides`.

    Overrides may contain 'extra_rules' (appended to the default rule list) and
    'disabled_rules' (removed from it); any other key replaces the default value.
    """
    cfg = copy.deepcopy(DEFAULTS)
    overrides = dict(overrides or {})
    extra = overrides.pop("extra_rules", None)
    disabled = set(overrides.pop("disabled_rules", ()))
    cfg.update(overrides)
    if extra:
        cfg["rules"] = list(extra)
    cfg["rules"] = [rule for rule in cfg["rules"] if rule not in disabled]
    return cfg
