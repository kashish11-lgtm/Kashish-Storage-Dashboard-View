"""
Assembles a per-subcategory (pst) dataset for the Subcategory Battlecard dashboard:
head-to-head comparison matrix + a deep-dive profile per subcategory, in the same
spirit as a competitive battlecard but applied to Storage & Organisers subcategories
racing each other for GMV share instead of competing companies.

Sources (all already produced by earlier build*.py scripts, kept as-is):
  subcategory_table_v3_juloy.csv  -> core matrix: gmv/share/yoy/cvr/asp/instock
  funnel_subcat.csv               -> funnel diagnosis + problem tags
  returns_by_pst.csv, cancel_by_pst.csv -> leakage rates
  priceband_x_subcat.csv          -> price-band GMV mix
  funnel_opportunity_pst.csv, conv_opp_subcat.csv -> $ opportunity sizing
  brand_yoy.json (keyed "category|pst") -> top brands within each subcategory

Output: subcat_battlecard_data.json, consumed by dashboard/subcategory_battlecard.html
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent

def read_csv(name):
    with open(HERE / name, newline="") as f:
        return list(csv.DictReader(f))

def num(v, default=0.0):
    if v is None or v == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default

subcat_rows = read_csv("subcategory_table_v3_juloy.csv")
funnel_rows = {r["pst"]: r for r in read_csv("funnel_subcat.csv")}
returns_rows = {r["pst"]: r for r in read_csv("returns_by_pst.csv")}
cancel_rows = {r["pst"]: r for r in read_csv("cancel_by_pst.csv")}
opp_rows = {r["pst"]: r for r in read_csv("funnel_opportunity_pst.csv")}
conv_opp_rows = {r["pst"]: r for r in read_csv("conv_opp_subcat.csv")}

price_band_cols = ["<25 AED", "25-50 AED", "50-100 AED", "100-200 AED", "200-400 AED", "400+ AED"]
priceband_rows = {r["pst"]: r for r in read_csv("priceband_x_subcat.csv")}

brand_yoy = json.load(open(HERE / "brand_yoy.json"))

def problem_tags(pst):
    r = funnel_rows.get(pst)
    if not r or not r.get("problem_tags"):
        return []
    raw = r["problem_tags"]
    try:
        import ast
        return ast.literal_eval(raw)
    except Exception:
        return [raw]

def top_brands(pst, n=8):
    key = next((k for k in brand_yoy if k.endswith("|" + pst)), None)
    if not key:
        return []
    brands = brand_yoy[key]
    ranked = sorted(brands.items(), key=lambda kv: kv[1].get("gmv26", 0), reverse=True)[:n]
    out = []
    for name, b in ranked:
        gmv25 = b.get("gmv25", 0) or 0
        gmv26 = b.get("gmv26", 0) or 0
        out.append({
            "brand": name,
            "gmv26": round(gmv26, 2),
            "gmv25": round(gmv25, 2),
            "growth_pct": b.get("growth"),
            "abs_chg": b.get("abs"),
        })
    return out

subcats = []
for r in subcat_rows:
    pst = r["pst"]
    fr = funnel_rows.get(pst, {})
    ret = returns_rows.get(pst, {})
    can = cancel_rows.get(pst, {})
    opp = opp_rows.get(pst, {})
    conv = conv_opp_rows.get(pst, {})
    pb = priceband_rows.get(pst, {})

    subcats.append({
        "pst": pst,
        "gmv_aug26": num(r["gmv_aug26"]),
        "gmv_aug25": num(r["gmv_aug25"]),
        "share_aug26": num(r["share_aug26"]),
        "share_aug25": num(r["share_aug25"]),
        "yoy_growth_pct": num(r["yoy_growth_pct"]),
        "abs_yoy_chg": num(r["abs_yoy_chg"]),
        "gv_yoy_pct": num(r["gv_yoy_pct"]),
        "cvr_aug26": num(r["cvr_aug26"]),
        "cvr_aug25": num(r["cvr_aug25"]),
        "cvr_yoy_pp": num(r["cvr_yoy_pp"]),
        "asp_aug26": num(r["asp_aug26"]),
        "asp_aug25": num(r["asp_aug25"]),
        "asp_yoy_pct": num(r["asp_yoy_pct"]),
        "instock_aug26": num(r["instock_aug26"]),
        "n_skus_aug26": num(r["n_skus_aug26"]),
        "selling_pct_aug26": num(r["selling_pct_aug26"]),
        "contribution_pct": num(r["contribution_pct"]),

        "funnel": {
            "gmv": num(fr.get("gmv")),
            "gv": num(fr.get("gv")),
            "orders": num(fr.get("orders")),
            "impressions": num(fr.get("impressions")),
            "atc": num(fr.get("atc")),
            "units": num(fr.get("units")),
            "instock_wtd": num(fr.get("instock_wtd")),
            "platform_gmv_loss": num(fr.get("platform_gmv_loss")),
            "ctr": num(fr.get("ctr")),
            "cvr": num(fr.get("cvr")),
            "atc_rate": num(fr.get("atc_rate")),
            "gv_share": num(fr.get("gv_share")),
        },
        "problem_tags": problem_tags(pst),

        "return_pct": num(ret.get("return_pct")),
        "cancel_pct": num(can.get("cancel_pct")),

        "price_band_mix": {b: num(pb.get(b)) for b in price_band_cols} if pb else {},

        "opportunity": {
            "loss_ctr": num(opp.get("loss_ctr")),
            "loss_conv": num(opp.get("loss_conv")),
            "loss_stock": num(opp.get("loss_stock")),
            "loss_total": num(opp.get("loss_total")),
            "opp_vs_jul": num(conv.get("opp_vs_jul")),
            "opp_vs_h1": num(conv.get("opp_vs_h1")),
        },

        "top_brands": top_brands(pst),
    })

subcats.sort(key=lambda s: s["gmv_aug26"], reverse=True)

out = {
    "generated_from": "ATLAS115_AE_Home_SKU_Monthly, Jan 2025-Aug 2026",
    "n_subcats": len(subcats),
    "subcats": subcats,
}

with open(HERE / "subcat_battlecard_data.json", "w") as f:
    json.dump(out, f, indent=1)

print(f"Wrote {len(subcats)} subcategories to subcat_battlecard_data.json")
print("Top 5 by GMV:", [s["pst"] for s in subcats[:5]])
