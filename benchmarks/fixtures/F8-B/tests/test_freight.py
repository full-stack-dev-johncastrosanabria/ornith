from decimal import Decimal as D

import pytest

from freight import RateError, Shipment, rate

CASES = [
    (Shipment('01020', '05999', D("0.8"), 20, 15, 10, 1), D("6.90")),
    (Shipment('12345', '90210', D("4.2"), 40, 30, 20, 3), D("28.25")),
    (Shipment('86001', '00500', D("2.0"), 30, 20, 10, 6), D("11.46")),
    (Shipment('48100', '48155', D("12.5"), 60, 40, 40, 8, 'ACME'), D("35.58")),
    (Shipment('24000', '72000', D("3.0"), 50, 50, 50, 11, 'standard', 'express'), D("217.08")),
    (Shipment('36000', '99999', D("0.4"), 10, 10, 5, 12), D("10.71")),
    (Shipment('60100', '12000', D("31.0"), 80, 60, 40, 2, 'GLOBEX'), D("151.90")),
    (Shipment('72500', '36500', D("9.9"), 130, 20, 20, 4), D("65.24")),
    (Shipment('00001', '86999', D("25.0"), 100, 50, 30, 7, 'INITECH', 'express'), D("166.60")),
    (Shipment('48000', '24000', D("5.0"), 60, 60, 60, 9, 'INITECH'), D("141.84")),
    (Shipment('12000', '60000', D("1.25"), 20, 20, 20, 5, 'UMBRELLA', 'express'), D("23.67")),
    (Shipment('99000', '11000', D("70"), 90, 50, 50, 10), D("215.92")),
    (Shipment('24000', '08542', D("3.3"), 25, 25, 25, 6), D("23.10")),
    (Shipment('24000', '08642', D("3.3"), 25, 25, 25, 6), D("23.10")),
]


@pytest.mark.parametrize("shipment,expected", CASES)
def test_rate(shipment, expected):
    assert rate(shipment) == expected


@pytest.mark.parametrize("shipment", [
    Shipment("1234", "12345", D("1"), 10, 10, 10, 1),
    Shipment("12345", "12345", D("0"), 10, 10, 10, 1),
    Shipment("12345", "12345", D("70.5"), 10, 10, 10, 1),
    Shipment("12345", "12345", D("1"), 10, 10, 10, 13),
    Shipment("12345", "12345", D("1"), 10, 10, 10, 1, "WAYNE"),
    Shipment("12345", "12345", D("1"), 10, 10, 10, 1, "standard", "air"),
    Shipment("12345", "12345", D("1"), 0, 10, 10, 1),
])
def test_invalid(shipment):
    with pytest.raises(RateError):
        rate(shipment)
