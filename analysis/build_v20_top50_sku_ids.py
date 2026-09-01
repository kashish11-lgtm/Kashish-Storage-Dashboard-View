import pandas as pd, json

d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month'] == '2026-08'].copy()
F = 30.4 / 16

g = aug.groupby(['sku', 'product_name']).agg(gmv=('gmv_aed', 'sum')).reset_index()
g['gmv_m'] = g['gmv'] * F
g = g.sort_values('gmv_m', ascending=False).head(50)

# sid keyed by (rounded gmv, product_name) so it can be matched positionally
# against the already-embedded TOP50_SKU array in the dashboard -- confirms
# the row order/values line up before the sid gets spliced in.
out = [{'gmv': round(r['gmv_m']), 'sid': r['sku']} for _, r in g.iterrows()]
with open('top50_sku_ids.json', 'w') as f:
    json.dump(out, f)
print(len(out), 'SKU IDs')
print(out[:3])
