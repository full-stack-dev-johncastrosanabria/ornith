"""Per-customer configuration overrides (see config.loader.load)."""

CUSTOMERS = {
    "c-100": {},
    "c-200": {"tier": "gold", "extra_rules": ["loyalty"]},
    "c-300": {"tier": "silver", "extra_rules": ["loyalty"], "disabled_rules": ["region_fee"]},
}
