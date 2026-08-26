# Storage & Organisers — Category Growth Diagnostic

A full category growth diagnostic for Noon's Storage & Organisers category (AE), built from
`ATLAS115_AE_Home_SKU_Monthly` — a continuous, gap-free series from **January 2025 through
August 2026** (657,723 SKU-month rows after filtering to the Storage & Organisers product
types), assembled from four source deliveries covering H1 2025, H2 2025, H1 2026 and the
partial H2 2026 (Jul–Aug) period.

## Contents

- **`dashboard/storage_diagnostic.html`** — the deliverable. A self-contained, single-page
  dashboard covering category health (with a true YoY decomposition), subcategory/price-band/
  brand/SKU breakdowns, funnel and stock leakage, seller and visibility analysis, real
  12+ month seasonality, a sized growth-opportunity universe, and a prioritized top-10 action
  plan with quantified GMV impact. Open directly in a browser.
- **`analysis/build*.py`** — the Python/pandas scripts used to derive every number on the
  dashboard from the raw source workbooks (not included in this repo; point the scripts at
  your local copies to regenerate). `build_v2_*.py` are the scripts behind the current
  (continuous-data) version of the dashboard; `build.py`–`build7.py` are the earlier scripts
  from before the full dataset was available, kept for reference.
- **`analysis/*.csv`, `analysis/*.json`** — intermediate summary tables (subcategory, price
  band, funnel, seller, SKU, decomposition, monthly trend) produced by the build scripts and
  used to source the dashboard's figures.

## Data notes

- August 2026 is a partial month (16 of ~31 days) in the source data; all monthly figures are
  shown as daily-rate, month-equivalent run-rates for comparability. Because of this, headline
  year-over-year comparisons use the last **complete** month (July 2026 vs July 2025) rather
  than a raw Aug'26-vs-Aug'25 comparison, which would be distorted for subcategories with
  within-month seasonality (e.g. Lunch Box's back-to-school peak typically lands in the back
  half of August).
- No competitor, ad-spend/ROAS, or ratings/reviews data exists in the source files — sections
  that would depend on it are flagged as explicit data gaps rather than estimated.
