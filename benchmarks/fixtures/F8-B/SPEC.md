# Parcel freight rating, version 3

This document specifies how the freight charge of a parcel shipment is computed. It replaces version 2 (see section 10, kept only for audit purposes). Amounts are in EUR. All arithmetic must be exact decimal arithmetic; binary floating point is not acceptable for money.

## 1. Background

Version 1 of the tariff was introduced when the network had four depots. The network now has eight regions and the tariff distinguishes six zones. Operations asked for a single, auditable calculation order (section 9) because earlier implementations applied surcharges and discounts in different orders. Customer service also reported disputes about volumetric weight on light, bulky parcels; section 4 settles them. Nothing in this background section changes the calculation.

## 2. Regions

A postal code has exactly five digits. Its region is determined by its first two digits:

| First two digits | Region |
|---|---|
| 00–11 | A |
| 12–23 | B |
| 24–35 | C |
| 36–47 | D |
| 48–59 | E |
| 60–71 | F |
| 72–85 | G |
| 86–99 | H |

Codes that are not exactly five digits are invalid (section 8).

## 3. Zones

The zone is looked up from the origin region (row) and the destination region (column). The table is symmetric.

| from \ to | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| A | 1 | 2 | 3 | 4 | 5 | 6 | 6 | 3 |
| B | 2 | 1 | 2 | 4 | 4 | 5 | 6 | 6 |
| C | 3 | 2 | 1 | 3 | 3 | 4 | 5 | 6 |
| D | 4 | 4 | 3 | 1 | 3 | 4 | 4 | 5 |
| E | 5 | 4 | 3 | 3 | 1 | 3 | 3 | 5 |
| F | 6 | 5 | 4 | 4 | 3 | 1 | 2 | 3 |
| G | 6 | 6 | 5 | 4 | 3 | 2 | 1 | 2 |
| H | 3 | 6 | 6 | 5 | 5 | 3 | 2 | 1 |

Note: the A–H corridor is zone 3 by agreement with the coastal carrier, although the regions are far apart.

## 4. Billable weight

1. Volumetric weight (kg) = length × width × height (cm) divided by the service divisor: **5000 for ground, 4000 for express**.
2. Billable weight is the largest of: the actual weight, the volumetric weight, and 1.0 kg.
3. The billable weight is then rounded **up** to the next multiple of 0.5 kg (a value that is already a multiple stays unchanged).

Example: an express parcel of 30×20×10 cm weighing 0.8 kg has a volumetric weight of 1.5 kg, so the billable weight is 1.5 kg.

## 5. Base tariff

The base charge for a zone and service is the price of the first kilogram plus the price of each additional 0.5 kg of billable weight above 1.0 kg.

| Zone | Ground first kg | Ground each extra 0.5 kg | Express first kg | Express each extra 0.5 kg |
|---|---|---|---|---|
| 1 | 6.25 | 0.82 | 11.25 | 1.31 |
| 2 | 7.10 | 1.04 | 12.78 | 1.66 |
| 3 | 7.95 | 1.26 | 14.31 | 2.02 |
| 4 | 8.80 | 1.48 | 15.84 | 2.37 |
| 5 | 9.65 | 1.70 | 17.37 | 2.72 |
| 6 | 10.50 | 1.92 | 18.90 | 3.07 |

## 6. Surcharges

### 6.1 Fuel

A fuel surcharge is a percentage of the **base charge** only. The percentage depends on the shipping month:

| Month | Fuel % |
|---|---|
| 1 | 8.75 |
| 2 | 8.5 |
| 3 | 9.25 |
| 4 | 9.0 |
| 5 | 9.25 |
| 6 | 9.5 |
| 7 | 10.25 |
| 8 | 10.5 |
| 9 | 10.25 |
| 10 | 10.5 |
| 11 | 10.25 |
| 12 | 11.0 |

### 6.2 Remote destinations

If the first three digits of the destination postal code are in the list below, add a flat 7.50.

085, 086, 131, 314, 349, 399, 451, 698, 757, 855, 923, 941.

### 6.3 Oversize

Add a flat 25.00 if the longest side exceeds 120 cm, or if the longest side plus twice the sum of the other two sides exceeds 300 cm. Oversize is charged at most once per parcel.

### 6.4 Heavy parcels

Add a flat 15.00 when the billable weight exceeds 30 kg.

## 7. Contract discounts

Shipments of contract customers receive a percentage discount on base + fuel. Flat surcharges (6.2–6.4) are never discounted. Customers that are not under contract use the code `standard` and get no discount.

| Contract | Ground % | Express % |
|---|---|---|
| ACME | 12 | 12 |
| GLOBEX | 8 | 8 |
| INITECH | 0 | 15 |
| UMBRELLA | 5 | 5 |

Any other customer code is invalid (section 8).

## 8. Validation

A shipment is invalid, and the rating must raise `RateError`, when: a postal code is not exactly five digits; the weight is not greater than 0 kg or is above 70 kg; any dimension is below 1 cm; the month is outside 1–12; the service is not `ground` or `express`; or the customer is neither `standard` nor a contract listed in section 7.

## 9. Calculation order

1. Validate the shipment (section 8).
2. Compute the billable weight (section 4).
3. Look up the zone from the origin and destination regions (sections 2 and 3).
4. Compute the base charge (section 5).
5. Add the fuel surcharge on the base charge (6.1).
6. Apply the contract discount to base + fuel (section 7).
7. Add the flat surcharges that apply (6.2, 6.3, 6.4).
8. Round the total half-up to 0.01.
9. If the result is below the minimum charge of **6.90**, charge 6.90.

## 10. Version 2 rules (DEPRECATED — do not implement)

Kept for audits of old invoices only. None of these rules apply to version 3:

- volumetric divisor 6000 for every service;
- totals rounded to 0.05;
- a minimum charge of 5.50;
- the fuel surcharge applied to the total after the remote surcharge;
- this obsolete fuel table:

| Month | Fuel % (v2) |
|---|---|
| 1 | 11.00 |
| 2 | 10.75 |
| 3 | 11.50 |
| 4 | 11.25 |
| 5 | 11.50 |
| 6 | 11.75 |
| 7 | 12.50 |
| 8 | 12.75 |
| 9 | 12.50 |
| 10 | 12.75 |
| 11 | 12.50 |
| 12 | 13.25 |

## 11. Glossary

- **Base charge**: first-kilogram price plus additional half-kilogram prices (section 5).
- **Billable weight**: the weight used for pricing after volumetric comparison and rounding (section 4).
- **Flat surcharge**: a fixed amount added after discounts (6.2–6.4).
