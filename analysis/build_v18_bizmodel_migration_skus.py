import pandas as pd, numpy as np, json, re

d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month'] == '2026-08'].copy()
aug['brand'] = aug['brand'].fillna('unbranded_generic')
F = 30.4 / 16

# Same FBN cancellation benchmark used everywhere else in the Seller
# Analysis section, and the same brand list/order as tbl-bizmodel-migration
# (BIZ_MIGRATION in the dashboard) -- SKU-level detail for those exact brands.
fbn = aug[aug['business_model'] == 'FBN']
fbn_cancel_pct = fbn['cancelled_gmv_aed'].sum() / fbn['gmv_aed'].sum()

BRANDS = ['famapy', 'chako_lab', 'mackenzie_childs', 'aiwanto', 'kovar',
          'dubaigallery', 'bentgo', 'marcolo', 'blooming_time', 'locknlock']


def clean_name(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    return s[:70] + '…' if len(s) > 70 else s


sku_details = {}
for brand in BRANDS:
    # SBB/DSE-fulfilled listings only -- the migration-candidate pool this
    # table is about (same scope as lowtier_gmv in build_v3_bizmodel3.py).
    s = aug[(aug['brand'] == brand) & (aug['business_model'].isin(['SBB', 'DSE']))]
    sg = s.groupby(['sku', 'product_name']).apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'cancelled': x['cancelled_gmv_aed'].sum(),
        'platform_loss': x['platform_gmv_loss_aed'].sum(),
        'instock': x['live_days'].sum() / x['days_in_month'].sum() * 100 if x['days_in_month'].sum() else 0,
        'units': x['units'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(),
        'impressions': x['impressions'].sum(),
    }), include_groups=False).reset_index()
    sg['cancel_pct'] = sg['cancelled'] / sg['gmv'].replace(0, np.nan) * 100
    sg['cvr'] = sg['orders'] / sg['gv'].replace(0, np.nan) * 100
    sg['cancel_recovery'] = np.maximum(0, sg['cancelled'] - sg['gmv'] * fbn_cancel_pct)
    sg['opp'] = sg['cancel_recovery'] + sg['platform_loss']
    sg = sg.sort_values('opp', ascending=False)
    sg = sg[(sg['gmv'] > 0) | (sg['opp'] > 0)].head(15)
    skus = []
    for _, sr in sg.iterrows():
        skus.append({
            'name': clean_name(sr['product_name']), 'sid': sr['sku'],
            'gmv': round(sr['gmv'] * F),
            'cancel_pct': round(sr['cancel_pct'], 1) if not pd.isna(sr['cancel_pct']) else 0,
            'instock': round(sr['instock'], 0), 'units': int(sr['units'] * F),
            'impressions': round(sr['impressions'] * F),
            'cvr': round(sr['cvr'], 1) if not pd.isna(sr['cvr']) else 0,
            'opp': round(sr['opp'] * F),
        })
    sku_details[brand] = skus

with open('bizmodel_migration_skus.json', 'w') as f:
    json.dump(sku_details, f)

for brand, skus in sku_details.items():
    print(brand, len(skus), 'SKUs, total opp', round(sum(s['opp'] for s in skus)))
