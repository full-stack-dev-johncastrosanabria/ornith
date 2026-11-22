from decimal import Decimal as D

import pytest

from warehouse.config.loader import load
from warehouse.models import Item, Order
from warehouse.pricing.engine import price
from warehouse.services.checkout import checkout_total


def order(customer, region, *items):
    return Order(customer, region, list(items))


def test_regular_order_gets_region_fee():
    assert checkout_total(order("c-100", "north", Item("A-1", 2, D("25.00")), Item("B-2", 1, D("50.00")))) == D("104.50")


def test_percentages_apply_before_fixed_fees_and_rounding():
    assert checkout_total(order("c-100", "south", Item("C-3", 60, D("1.99")))) == D("119.45")


def test_complete_bundle_discount():
    assert checkout_total(order("c-100", "north", Item("K-1", 1, D("40.00"), "B1"), Item("K-2", 1, D("60.00"), "B1"), Item("Z-9", 1, D("10.00")))) == D("99.50")


def test_one_product_is_not_a_bundle():
    assert checkout_total(order("c-100", "north", Item("K-1", 3, D("40.00"), "B1"))) == D("124.50")


def test_gold_customer_keeps_default_rules():
    assert checkout_total(order("c-200", "north", Item("K-1", 1, D("40.00"), "B1"), Item("K-2", 1, D("60.00"), "B1"), Item("C-3", 50, D("1.00")))) == D("123.10")


def test_disabled_rule_is_removed():
    assert checkout_total(order("c-300", "islands", Item("A-1", 4, D("12.50")))) == D("48.50")


def test_extra_rules_extend_defaults():
    rules = load({"extra_rules": ["loyalty"]})["rules"]
    assert rules[:4] == ["bulk", "bundle", "region_fee", "rounding"] and "loyalty" in rules


def test_unknown_rule_is_rejected():
    with pytest.raises(KeyError):
        price(order("c-100", "north", Item("A-1", 1, D("1.00"))), load({"extra_rules": ["does-not-exist"]}))


def test_total_has_two_decimals():
    assert checkout_total(order("c-100", "north", Item("R-1", 1, D("10.02")))).as_tuple().exponent == -2
