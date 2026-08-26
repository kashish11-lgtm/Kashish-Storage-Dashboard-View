import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
AUG='2026-08'
aug = d[d['month']==AUG].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')
bins=[0,25,50,100,200,400,np.inf]; labels=['<25','25-50','50-100','100-200','200-400','400+']
aug['pb']=pd.cut(aug['offer_price_aed'], bins=bins, labels=labels, right=False)

# PST x price band: CVR
top_psts = aug.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False).head(10).index.tolist()
g = aug[aug['pst'].isin(top_psts)].groupby(['pst','pb'], observed=True).apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum()
}), include_groups=False)
g['cvr']=g['orders']/g['gv'].replace(0,np.nan)*100
best = g.reset_index().sort_values(['pst','cvr'], ascending=[True,False]).groupby('pst').first()
print("Best-converting price band per top-10 subcategory:")
pd.set_option('display.width',200)
print(best[['pb','cvr','gmv']].round(1))

# Brand x price band for top brands overall
top_brands = aug[~aug['brand'].isin(['unbranded_generic','generic'])].groupby('brand')['gmv_aed'].sum().sort_values(ascending=False).head(15).index.tolist()
gb = aug[aug['brand'].isin(top_brands)].groupby(['brand','pb'], observed=True).apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum()
}), include_groups=False)
gb['cvr']=gb['orders']/gb['gv'].replace(0,np.nan)*100
bestb = gb.reset_index().sort_values(['brand','gmv'], ascending=[True,False]).groupby('brand').first()
print("\nDominant (highest-GMV) price band per top-15 brand:")
print(bestb[['pb','gmv','cvr']].round(1))
g.to_csv('pst_priceband_cvr.csv')
gb.to_csv('brand_priceband.csv')
