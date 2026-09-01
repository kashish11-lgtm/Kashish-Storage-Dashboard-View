import pandas as pd, numpy as np, json

d = pd.read_parquet('storage_full_v2.parquet')
recent = d[d['month'].isin(['2026-06','2026-07','2026-08'])].copy()
DAYS = 30+31+31
F = 30.4/DAYS

bins=[0,25,50,100,200,400,np.inf]; labels=['<25 AED','25-50 AED','50-100 AED','100-200 AED','200-400 AED','400+ AED']
recent['pb'] = pd.cut(recent['offer_price_aed'], bins=bins, labels=labels, right=False)

def top_band_by_gmv(df, group_col, min_gmv=500):
    """For each group, the price band with the HIGHEST GMV (not CVR --
    CVR is mechanically higher in cheap bands, so 'best-converting' always
    picks the entry tier and says nothing about where the money is)."""
    g = df.groupby([group_col,'pb'], observed=True).apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(),
    }), include_groups=False).reset_index()
    g['cvr'] = g['orders']/g['gv'].replace(0,np.nan)*100
    tot = g.groupby(group_col)['gmv'].sum()
    rows = []
    for name, sub in g.groupby(group_col):
        total_gmv = tot.get(name,0)
        if total_gmv*F < min_gmv: continue
        best = sub.loc[sub['gmv'].idxmax()]
        if best['gmv'] <= 0: continue
        rows.append({
            'name': name, 'band': str(best['pb']),
            'gmv': round(best['gmv']*F), 'cvr': round(best['cvr'],1) if pd.notna(best['cvr']) else 0,
            'share_of_total': round(best['gmv']/total_gmv*100,1) if total_gmv else 0,
            'total_gmv': round(total_gmv*F),
        })
    rows.sort(key=lambda r:-r['total_gmv'])
    return rows

# subcategory level -- all psts with meaningful GMV
pst_rows = top_band_by_gmv(recent, 'pst', min_gmv=500)
for r in pst_rows:
    r['name'] = r['name'].replace('_',' ').title()
print(f"{len(pst_rows)} subcategories")
for r in pst_rows[:15]:
    print(f"  {r['name']:32s} {r['band']:12s} GMV {r['gmv']:>7,} ({r['share_of_total']:.0f}% of its total)  CVR there {r['cvr']}%")

# brand level -- top 40 brands by total GMV
recent['brand'] = recent['brand'].fillna('unbranded_generic')
brand_totals = recent[recent['brand']!='unbranded_generic'].groupby('brand')['gmv_aed'].sum().sort_values(ascending=False)
top_brands = brand_totals.head(40).index.tolist()
brand_rows = top_band_by_gmv(recent[recent['brand'].isin(top_brands)], 'brand', min_gmv=500)
print(f"\n{len(brand_rows)} brands")
for r in brand_rows[:10]:
    print(f"  {r['name']:20s} {r['band']:12s} GMV {r['gmv']:>7,} ({r['share_of_total']:.0f}% of its total)  CVR there {r['cvr']}%")

OUT = {'pst': pst_rows, 'brand': brand_rows}
with open('pricepoint_bygmv.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
