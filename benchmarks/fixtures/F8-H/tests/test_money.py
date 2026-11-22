import ast
import pathlib

from billing.discounts import coupon_cents
from billing.exports.csv_export import csv_row
from billing.exports.ledger import ledger_entries
from billing.gateways.bank import transfer_cents
from billing.gateways.card import capture_payload
from billing.invoices import invoice_label, invoice_total_cents, line_cents
from billing.refunds import refund_cents
from billing.reports.summary import summary_line
from billing.subscriptions import monthly_cents
from billing.taxes import tax_cents
from billing.utils.money import format_cents, to_cents


def test_to_cents_is_exact():
    assert [to_cents(x) for x in (0.29, 2.675, 1.005, 19.99, "0.125", 7)] == [29, 268, 101, 1999, 13, 700]


def test_invoices():
    assert line_cents(3, 0.29) == 87
    assert invoice_total_cents([(1, 2.675), (2, 19.99)]) == 4266
    assert invoice_label([(1, 1.005)]) == "TOTAL 1.01"


def test_refunds_and_discounts():
    assert refund_cents(19.99, 0.29) == 1970
    assert coupon_cents(2.675) == 268


def test_subscriptions():
    assert monthly_cents("team", 3) == 5997
    assert monthly_cents("pro") == 2675


def test_taxes():
    assert tax_cents("19.99", "0.21") == 420
    assert tax_cents("2.675", "1") == 268


def test_exports_and_gateways():
    assert csv_row("INV-1", 0.29) == "INV-1,29"
    assert ledger_entries([("sales", 19.99), ("fees", 1.005)]) == [("sales", 1999), ("fees", 101)]
    assert capture_payload(2.675) == {"amount": 268, "currency": "EUR"}
    assert transfer_cents([0.29, 0.29, 19.99]) == 2057
    assert summary_line("day", [2.675, 0.29]) == "day: 2.97"
    assert format_cents(-5) == "-0.05"


def test_legacy_helper_is_gone():
    root = pathlib.Path(__file__).resolve().parents[1] / "billing"
    hits = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            name = getattr(node, "id", None) or getattr(node, "attr", None) or getattr(node, "name", None)
            if name == "to_cents_legacy" or (isinstance(node, ast.alias) and node.name == "to_cents_legacy"):
                hits.append(f"{path.name}:{getattr(node, 'lineno', '?')}")
    assert hits == []
