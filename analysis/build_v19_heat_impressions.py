import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month'] == '2026-08'].copy()
bins = [0, 25, 50, 100, 200, 400, np.inf]; labels = ['<25', '25-50', '50-100', '100-200', '200-400', '400+']
aug['pb'] = pd.cut(aug['offer_price_aed'], bins=bins, labels=labels, right=False)
F = 30.4 / 31

# same subcategory list/order as the GMV heat matrix (build_v11_heat_all.py) --
# every subcategory present in Aug'26
pst_gmv = aug.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False)
all_psts = pst_gmv.index.tolist()

aug25 = d[d['month'] == '2025-08'].copy()
aug25['pb'] = pd.cut(aug25['offer_price_aed'], bins=bins, labels=labels, right=False)
F25 = 30.4 / 31

# heat matrix: pst x band impressions
mat = aug[aug['pst'].isin(all_psts)].pivot_table(index='pst', columns='pb', values='impressions', aggfunc='sum', observed=True).reindex(all_psts)[labels].fillna(0) * F
mat = mat.round(0).astype(int)

# SKU count per (pst, band) cell with impressions>0 -- the "getting demand" count
sku_mat = aug[(aug['pst'].isin(all_psts)) & (aug['impressions'] > 0)].pivot_table(
    index='pst', columns='pb', values='sku', aggfunc='nunique', observed=True
).reindex(all_psts)[labels].fillna(0).astype(int)

mat25 = aug25.pivot_table(index='pst', columns='pb', values='impressions', aggfunc='sum', observed=True).reindex(all_psts)[labels].fillna(0) * F25
sku_mat25 = aug25[aug25['impressions'] > 0].pivot_table(
    index='pst', columns='pb', values='sku', aggfunc='nunique', observed=True
).reindex(all_psts)[labels].fillna(0)


def yoy_matrix(cur, prev):
    out = []
    for i in range(len(cur)):
        row = []
        for j in range(len(cur[i])):
            c, p = cur[i][j], prev.values[i][j]
            if p <= 0:
                row.append(None if c <= 0 else 'new')
            else:
                row.append(round((c - p) / p * 100, 1))
        out.append(row)
    return out


def prev_matrix(prev):
    return [[int(v) for v in row] for row in prev.values.tolist()]


HEAT_IMPR_DATA = mat.values.tolist()
HEAT_IMPR_SKUS = sku_mat.values.tolist()
HEAT_IMPR_YOY = yoy_matrix(HEAT_IMPR_DATA, mat25)
HEAT_IMPR_SKU_PREV = prev_matrix(sku_mat25)

OUT = {'data': HEAT_IMPR_DATA, 'skus': HEAT_IMPR_SKUS, 'yoy': HEAT_IMPR_YOY, 'skuPrev': HEAT_IMPR_SKU_PREV}
with open('heat_impressions.json', 'w') as f:
    json.dump(OUT, f, separators=(',', ':'))
import os
print('size KB', os.path.getsize('heat_impressions.json') / 1024)
print('subcats', len(all_psts))
print('total category impressions check:', mat.values.sum(), 'vs', round(aug['impressions'].sum() * F))
