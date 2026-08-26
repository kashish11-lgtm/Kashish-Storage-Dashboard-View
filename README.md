# Storage & Organisers — Category Growth Diagnostic

A full category growth diagnostic for Noon's Storage & Organisers category (AE), built from
`ATLAS115_AE_Home_SKU_Monthly` (Jan–Jun 2025 + Jul–Aug 2026, 235,933 SKU-month rows).

## Contents

- **`dashboard/storage_diagnostic.html`** — the deliverable. A self-contained, single-page
  dashboard covering category health, subcategory/price-band/brand/SKU breakdowns, funnel
  and stock leakage, seller and visibility analysis, a sized growth-opportunity universe, and
  a prioritized top-10 action plan with quantified GMV impact. Open directly in a browser.
- **`analysis/build*.py`** — the Python/pandas scripts used to derive every number on the
  dashboard from the raw source workbooks (not included in this repo; point `build.py` at
  your local copies to regenerate).
- **`analysis/*.csv`, `analysis/*.json`** — intermediate summary tables (subcategory, price
  band, funnel, seller, SKU, decomposition) produced by the build scripts and used to source
  the dashboard's figures.

## Data notes

- The two source files cover Jan–Jun 2025 and Jul–Aug 2026 only, with a 12-month gap between
  them, so there is no true calendar year-over-year comparison. The dashboard uses MoM
  (Aug'26 vs Jul'26) and "vs FY25 H1 average" as the closest available baseline instead —
  this is called out on the page itself.
- August 2026 is a partial month (16 days) in the source data; all monthly figures are shown
  as daily-rate, month-equivalent run-rates for comparability.
- No competitor, ad-spend/ROAS, or ratings/reviews data exists in the source files — sections
  that would depend on it are flagged as explicit data gaps rather than estimated.
