import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month']=='2026-08'].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')
bins=[0,25,50,100,200,400,np.inf]; labels=['<25','25-50','50-100','100-200','200-400','400+']
aug['pb']=pd.cut(aug['offer_price_aed'], bins=bins, labels=labels, right=False)
F = 30.4/16

# Aug'25 (full month, same calendar month one year back) for per-cell GMV/SKU
# YoY -- monthly-equivalent normalized the same way so the two are comparable
aug25 = d[d['month']=='2025-08'].copy()
aug25['pb'] = pd.cut(aug25['offer_price_aed'], bins=bins, labels=labels, right=False)
F25 = 30.4/31

# every subcategory present in Aug'26 (44 of 45 total -- garment_rack has zero
# rows in any 2026 month, only a single stray Feb'25 row, so it's excluded as
# having no current-period presence at all rather than by a GMV filter)
pst_gmv = aug.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False)
all_psts = pst_gmv.index.tolist()
print(f"{len(all_psts)} subcategories total ({(pst_gmv>0).sum()} with GMV>0 in Aug'26)")

# also need pt for each pst (for DRILL key matching used elsewhere)
pst_to_pt = aug.groupby('pst')['pt'].agg(lambda x: x.mode().iloc[0]).to_dict()

# heat matrix: pst x band GMV
mat = aug[aug['pst'].isin(all_psts)].pivot_table(index='pst', columns='pb', values='gmv_aed', aggfunc='sum', observed=True).reindex(all_psts)[labels].fillna(0)*F
mat = mat.round(0).astype(int)

# selling SKU count per (pst, band) cell -- distinct SKUs with GMV>0 in that cell
sku_mat = aug[(aug['pst'].isin(all_psts)) & (aug['gmv_aed']>0)].pivot_table(
    index='pst', columns='pb', values='sku', aggfunc='nunique', observed=True
).reindex(all_psts)[labels].fillna(0).astype(int)

# total LISTED SKU count per (pst, band) cell -- no gmv filter, so this
# includes SKUs that were live/listed in that band but didn't sell
sku_total_mat = aug[aug['pst'].isin(all_psts)].pivot_table(
    index='pst', columns='pb', values='sku', aggfunc='nunique', observed=True
).reindex(all_psts)[labels].fillna(0).astype(int)

# same matrices for Aug'25, to compute per-cell YoY / show last-year counts against
mat25 = aug25.pivot_table(index='pst', columns='pb', values='gmv_aed', aggfunc='sum', observed=True).reindex(all_psts)[labels].fillna(0)*F25
sku_mat25 = aug25[aug25['gmv_aed']>0].pivot_table(
    index='pst', columns='pb', values='sku', aggfunc='nunique', observed=True
).reindex(all_psts)[labels].fillna(0)
sku_total_mat25 = aug25.pivot_table(
    index='pst', columns='pb', values='sku', aggfunc='nunique', observed=True
).reindex(all_psts)[labels].fillna(0)

def yoy_matrix(cur, prev):
    """null where prev==0 and cur==0 (nothing to compare, cell is empty both
    years); 'new' where prev==0 and cur>0 (no base to grow from -- avoid a
    fabricated +inf%); a rounded numeric % otherwise."""
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
    """The raw prior-year count itself (not a delta or %%) -- shown as
    'N last year' so the reader sees both numbers plainly."""
    return [[int(v) for v in row] for row in prev.values.tolist()]

HEAT_SUBS = [p.replace('_',' ').title() for p in all_psts]
HEAT_KEYS = all_psts
HEAT_DATA = mat.values.tolist()
HEAT_SKUS = sku_mat.values.tolist()
HEAT_GMV_YOY = yoy_matrix(HEAT_DATA, mat25)
HEAT_SKU_PREV = prev_matrix(sku_mat25)
HEAT_SKU_TOTAL = sku_total_mat.values.tolist()
HEAT_SKU_TOTAL_PREV = prev_matrix(sku_total_mat25)

# SKU counts at brand level -- Jul+Aug 2026 combined, a SKU counts if it either
# has inventory (live_days>0, i.e. was listed/orderable at some point) or has
# sales (gmv_aed>0) in either month; deduplicated across the two months.
julaug = d[d['month'].isin(['2026-07','2026-08'])].copy()
julaug['brand'] = julaug['brand'].fillna('unbranded_generic')
julaug_active = julaug[(julaug['live_days']>0) | (julaug['gmv_aed']>0)]
brand_sku_counts = julaug_active.groupby(['pst','brand'])['sku'].nunique()

# brand x band matrix for ALL psts (top 20 brands each) -- reuse for click-to-expand
PST_BRAND_BAND = {}
for pst in all_psts:
    s = aug[aug['pst']==pst]
    top_brands = s[~s['brand'].isin(['unbranded_generic'])].groupby('brand')['gmv_aed'].sum().sort_values(ascending=False).head(20).index.tolist()
    m = {}
    for br in top_brands:
        row = {}
        bd = s[s['brand']==br]
        for band in labels:
            v = bd[bd['pb']==band]['gmv_aed'].sum()*F
            if v>0: row[band]=round(v)
        total = bd['gmv_aed'].sum()*F
        skus = int(brand_sku_counts.get((pst,br), 0))
        if total>0: m[br] = {'total': round(total), 'bands': row, 'skus': skus}
    if m: PST_BRAND_BAND[pst] = m

OUT = {'subs':HEAT_SUBS, 'keys':HEAT_KEYS, 'pts':[pst_to_pt[p] for p in all_psts], 'data':HEAT_DATA, 'skus':HEAT_SKUS, 'gmvYoy':HEAT_GMV_YOY, 'skuPrev':HEAT_SKU_PREV, 'skuTotal':HEAT_SKU_TOTAL, 'skuTotalPrev':HEAT_SKU_TOTAL_PREV, 'brandband':PST_BRAND_BAND}
with open('heat_all.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
import os
print('size KB', os.path.getsize('heat_all.json')/1024)
print('total category gmv check:', mat.values.sum(), 'vs', round(aug['gmv_aed'].sum()*F))
