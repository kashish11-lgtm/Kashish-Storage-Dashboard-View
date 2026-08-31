import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
AUG = '2026-08'
aug = d[d['month'] == AUG].copy()
F = 30.4 / 16

# category-wide Aug'26 funnel benchmarks (monthly-equivalent)
impr = aug['impressions'].sum() * F
gv = aug['gv'].sum() * F
atc = aug['atc'].sum() * F
orders = aug['orders'].sum() * F
gmv_cat = aug['gmv_aed'].sum() * F
cat_ctr = gv / impr
cat_atcr = atc / gv
cat_cvr = orders / gv
cat_aov = gmv_cat / orders

pst_to_pt = aug.groupby('pst')['pt'].agg(lambda x: x.mode().iloc[0]).to_dict()

pst = aug.groupby('pst').apply(lambda x: pd.Series({
    'impr': x['impressions'].sum(), 'gv': x['gv'].sum(), 'atc': x['atc'].sum(), 'orders': x['orders'].sum(),
    'gmv': x['gmv_aed'].sum(), 'platform_loss': x['platform_gmv_loss_aed'].sum(), 'express_loss': x['express_gmv_loss_aed'].sum(),
    'asp': x['gmv_aed'].sum() / x['units'].sum() if x['units'].sum() else 0,
}), include_groups=False)
pst = pst[pst['impr'] > 20000]  # meaningful-traffic subcats only
pst['ctr'] = pst['gv'] / pst['impr']
pst['atcr'] = pst['atc'] / pst['gv'].replace(0, np.nan)
pst['cvr'] = pst['orders'] / pst['gv'].replace(0, np.nan)
pst['aov'] = pst['gmv'] / pst['orders'].replace(0, np.nan)

# B: GMV left on the table if this pst's traffic converted to visits at the
# category CTR, using the pst's own downstream cvr/aov to value the extra visits
pst['loss_ctr'] = np.maximum(0, (pst['impr'] * cat_ctr - pst['gv'])) * pst['cvr'].fillna(cat_cvr) * pst['aov'].fillna(cat_aov)

# C: GMV left on the table at ATC stage (visits not adding to cart) and at CVR
# stage (ATC not converting to orders) -- worse of the two, since a subcat
# rarely leaks meaningfully at both simultaneously
pst['ord_per_atc'] = pst['orders'] / pst['atc'].replace(0, np.nan)
pst['loss_atc'] = np.maximum(0, (pst['gv'] * cat_atcr - pst['atc'])) * pst['ord_per_atc'].fillna(pst['cvr'] / cat_atcr) * pst['aov'].fillna(cat_aov)
pst['loss_cvr'] = np.maximum(0, (pst['gv'] * cat_cvr - pst['orders'])) * pst['aov'].fillna(cat_aov)
pst['loss_conv'] = pst[['loss_atc', 'loss_cvr']].max(axis=1)

# D: measured (not modelled) GMV lost to being out of stock
pst['loss_stock'] = pst['platform_loss'] + pst['express_loss']

for c in ['loss_ctr', 'loss_atc', 'loss_cvr', 'loss_conv', 'loss_stock']:
    pst[c] = pst[c] * F
pst['gmv'] = pst['gmv'] * F
pst['loss_total'] = pst['loss_ctr'] + pst['loss_conv'] + pst['loss_stock']
pst = pst.sort_values('loss_total', ascending=False)

rows = []
for pst_name, r in pst.iterrows():
    rows.append({
        'name': pst_name.replace('_', ' ').title(),
        'key': pst_to_pt.get(pst_name, '') + '|' + pst_name,
        'gmv': round(r['gmv']),
        'ctr': round(r['loss_ctr']),
        'conv': round(r['loss_conv']),
        'atc_or_cvr': 'atc' if r['loss_atc'] >= r['loss_cvr'] else 'cvr',
        'stock': round(r['loss_stock']),
        'total': round(r['loss_total']),
    })

with open('funnel_opportunity.json', 'w') as f:
    json.dump(rows, f)

print(len(rows), 'subcategories')
print('bucket totals -- B (ctr):', round(pst['loss_ctr'].sum()),
      'C (conv):', round(pst['loss_conv'].sum()),
      'D (stock):', round(pst['loss_stock'].sum()))
pd.set_option('display.width', 200)
print(pst[['gmv', 'loss_ctr', 'loss_conv', 'loss_stock', 'loss_total']].round(0).head(20))
