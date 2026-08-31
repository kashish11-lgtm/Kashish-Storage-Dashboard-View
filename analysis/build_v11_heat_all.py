import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month']=='2026-08'].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')
bins=[0,25,50,100,200,400,np.inf]; labels=['<25','25-50','50-100','100-200','200-400','400+']
aug['pb']=pd.cut(aug['offer_price_aed'], bins=bins, labels=labels, right=False)
F = 30.4/16

# all psts with meaningful GMV (drop the ~0 noise ones like carton/compost/clamshells)
pst_gmv = aug.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False)
all_psts = pst_gmv[pst_gmv>0].index.tolist()
print(f"{len(all_psts)} subcategories with GMV > 0 (of {aug['pst'].nunique()} total)")

# also need pt for each pst (for DRILL key matching used elsewhere)
pst_to_pt = aug.groupby('pst')['pt'].agg(lambda x: x.mode().iloc[0]).to_dict()

# heat matrix: pst x band GMV
mat = aug[aug['pst'].isin(all_psts)].pivot_table(index='pst', columns='pb', values='gmv_aed', aggfunc='sum', observed=True).reindex(all_psts)[labels].fillna(0)*F
mat = mat.round(0).astype(int)

HEAT_SUBS = [p.replace('_',' ').title() for p in all_psts]
HEAT_KEYS = all_psts
HEAT_DATA = mat.values.tolist()

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
        if total>0: m[br] = {'total': round(total), 'bands': row}
    if m: PST_BRAND_BAND[pst] = m

OUT = {'subs':HEAT_SUBS, 'keys':HEAT_KEYS, 'pts':[pst_to_pt[p] for p in all_psts], 'data':HEAT_DATA, 'brandband':PST_BRAND_BAND}
with open('heat_all.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
import os
print('size KB', os.path.getsize('heat_all.json')/1024)
print('total category gmv check:', mat.values.sum(), 'vs', round(aug['gmv_aed'].sum()*F))
