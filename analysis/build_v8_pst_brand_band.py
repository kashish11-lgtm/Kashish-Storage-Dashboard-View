import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month']=='2026-08'].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')
bins=[0,25,50,100,200,400,np.inf]; labels=['<25','25-50','50-100','100-200','200-400','400+']
aug['pb']=pd.cut(aug['offer_price_aed'], bins=bins, labels=labels, right=False)
F = 30.4/16

top_psts = aug.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False).head(10).index.tolist()
OUT = {}
for pst in top_psts:
    s = aug[aug['pst']==pst]
    top_brands = s[~s['brand'].isin(['unbranded_generic'])].groupby('brand')['gmv_aed'].sum().sort_values(ascending=False).head(20).index.tolist()
    # include generic too if it's big
    gmv_generic = s[s['brand']=='unbranded_generic']['gmv_aed'].sum()
    brands = top_brands
    mat = {}
    for br in brands:
        row = {}
        bd = s[s['brand']==br]
        for band in labels:
            v = bd[bd['pb']==band]['gmv_aed'].sum()*F
            if v>0: row[band]=round(v)
        total = bd['gmv_aed'].sum()*F
        mat[br] = {'total': round(total), 'bands': row}
    OUT[pst] = mat
    print(pst, len(brands), 'brands')

with open('pst_brand_band.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
import os
print('size KB', os.path.getsize('pst_brand_band.json')/1024)
