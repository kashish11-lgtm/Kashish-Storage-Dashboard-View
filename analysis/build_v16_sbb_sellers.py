import pandas as pd, numpy as np, json, re
d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month'] == '2026-08'].copy()
F = 30.4 / 16

# FBN cancellation benchmark -- the "if fulfilled well" baseline used
# consistently elsewhere in the Seller Analysis section
fbn = aug[aug['business_model'] == 'FBN']
fbn_cancel_pct = fbn['cancelled_gmv_aed'].sum() / fbn['gmv_aed'].sum()

sbb = aug[aug['business_model'] == 'SBB'].copy()
g = sbb.groupby('partner_name').agg(
    gmv=('gmv_aed', 'sum'), impressions=('impressions', 'sum'), search_impressions=('search_impressions', 'sum'),
    gv=('gv', 'sum'), atc=('atc', 'sum'), orders=('orders', 'sum'), units=('units', 'sum'),
    cancelled=('cancelled_gmv_aed', 'sum'), platform_loss=('platform_gmv_loss_aed', 'sum'), express_loss=('express_gmv_loss_aed', 'sum'),
    live_days=('live_days', 'sum'), days_in_month=('days_in_month', 'sum'), n_sku=('sku', 'nunique'),
).reset_index()
g = g[g['impressions'] > 0]  # "getting impressions" -- real demand exists, not a dead listing
g['cvr'] = g['orders'] / g['gv'].replace(0, np.nan) * 100
g['ctr'] = g['gv'] / g['impressions'] * 100
g['atc_rate'] = g['atc'] / g['gv'].replace(0, np.nan) * 100
g['cancel_pct'] = g['cancelled'] / g['gmv'].replace(0, np.nan) * 100
g['instock'] = g['live_days'] / g['days_in_month'].replace(0, np.nan) * 100
# Uplift = cancelled GMV in excess of the FBN cancellation benchmark, plus the
# stockout GMV already measured on this seller's SKUs -- what this seller
# would plausibly keep if their listings moved to FBN/DSE fulfilment,
# holding demand (impressions/GV) constant.
g['excess_cancel'] = np.maximum(0, g['cancelled'] - g['gmv'] * fbn_cancel_pct)
g['stock_loss'] = g['platform_loss'] + g['express_loss']
g['uplift'] = g['excess_cancel'] + g['stock_loss']
for c in ['gmv', 'impressions', 'search_impressions', 'gv', 'atc', 'units', 'uplift', 'excess_cancel', 'stock_loss']:
    g[c] = g[c] * F
g = g.sort_values('uplift', ascending=False)
top20 = g.head(20).copy()


def clean_name(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    return s[:70] + '…' if len(s) > 70 else s


rows = []
sku_details = {}
for _, r in top20.iterrows():
    seller = r['partner_name']
    rows.append({
        'name': seller,
        'gmv': round(r['gmv']), 'impressions': round(r['impressions']),
        'si_share': round(r['search_impressions'] / r['impressions'] * 100, 1) if r['impressions'] else 0,
        'gv': round(r['gv']), 'ctr': round(r['ctr'], 2), 'atc': round(r['atc']), 'atc_rate': round(r['atc_rate'], 1),
        'units': round(r['units']), 'cvr': round(r['cvr'], 2), 'cancel_pct': round(r['cancel_pct'], 1),
        'instock': round(r['instock'], 1), 'n_sku': int(r['n_sku']), 'uplift': round(r['uplift']),
    })
    # SKU-level breakdown for this seller, ranked by its own uplift -- "which
    # SKUs to push to Express/FBN/DSE first" within this seller's catalog
    s = sbb[sbb['partner_name'] == seller]
    sg = s.groupby(['sku', 'product_name']).apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'cancelled': x['cancelled_gmv_aed'].sum(),
        'platform_loss': x['platform_gmv_loss_aed'].sum(), 'express_loss': x['express_gmv_loss_aed'].sum(),
        'instock': x['live_days'].sum() / x['days_in_month'].sum() * 100 if x['days_in_month'].sum() else 0,
        'units': x['units'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(),
    }), include_groups=False).reset_index()
    sg['cancel_pct'] = sg['cancelled'] / sg['gmv'].replace(0, np.nan) * 100
    sg['excess_cancel'] = np.maximum(0, sg['cancelled'] - sg['gmv'] * fbn_cancel_pct)
    sg['stock_loss'] = sg['platform_loss'] + sg['express_loss']
    sg['uplift'] = sg['excess_cancel'] + sg['stock_loss']
    sg['cvr'] = sg['orders'] / sg['gv'].replace(0, np.nan) * 100
    sg = sg.sort_values('uplift', ascending=False)
    sg = sg[(sg['gmv'] > 0) | (sg['uplift'] > 0)].head(15)
    skus = []
    for _, sr in sg.iterrows():
        skus.append({
            'name': clean_name(sr['product_name']), 'sid': sr['sku'],
            'gmv': round(sr['gmv'] * F), 'cancel_pct': round(sr['cancel_pct'], 1) if not pd.isna(sr['cancel_pct']) else 0,
            'instock': round(sr['instock'], 0), 'units': int(sr['units'] * F),
            'cvr': round(sr['cvr'], 1) if not pd.isna(sr['cvr']) else 0,
            'uplift': round(sr['uplift'] * F),
        })
    sku_details[seller] = skus

with open('sbb_migration_sellers.json', 'w') as f:
    json.dump({'sellers': rows, 'skus': sku_details}, f)

print(len(rows), 'top SBB sellers by uplift')
print('total uplift, top 20:', round(sum(r['uplift'] for r in rows)))
print('total uplift, all SBB sellers w/ impressions:', round(g['uplift'].sum()))
pd.set_option('display.width', 220)
print(top20[['partner_name', 'gmv', 'impressions', 'gv', 'atc', 'units', 'cvr', 'cancel_pct', 'instock', 'uplift']].round(1).head(20))
