import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
d['brand']=d['brand'].fillna('unbranded_generic')
recent = d[d['month'].isin(['2026-06','2026-07','2026-08'])].copy()
bins=[0,25,50,100,200,400,np.inf]; labels=['<25','25-50','50-100','100-200','200-400','400+']
recent['pb']=pd.cut(recent['offer_price_aed'], bins=bins, labels=labels, right=False)

top_psts = recent.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False).head(10).index.tolist()
g = recent[recent['pst'].isin(top_psts)].groupby(['pst','pb'], observed=True).apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'gv':x['gv'].sum(),'orders':x['orders'].sum()}), include_groups=False)
g['cvr']=g['orders']/g['gv'].replace(0,np.nan)*100
g = g[g['gv']>=300]
best = g.reset_index().sort_values(['pst','cvr'], ascending=[True,False]).groupby('pst').first()
pd.set_option('display.width',200)
print("Best-converting price band per top-10 subcategory (Jun-Aug 2026, min 300 visits):")
print(best[['pb','cvr','gmv']].round(1))

top_brands = recent[~recent['brand'].isin(['unbranded_generic','generic'])].groupby('brand')['gmv_aed'].sum().sort_values(ascending=False).head(30).index.tolist()
gb = recent[recent['brand'].isin(top_brands)].groupby(['brand','pb'], observed=True).apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'gv':x['gv'].sum(),'orders':x['orders'].sum()}), include_groups=False)
gb['cvr']=gb['orders']/gb['gv'].replace(0,np.nan)*100
gb=gb[gb['gv']>=100]
bestb = gb.reset_index().sort_values(['brand','cvr'],ascending=[True,False]).groupby('brand').first()
print("\nBest-converting price band per top-30 brand (Jun-Aug 2026, min 100 visits):")
print(bestb[['pb','cvr','gmv']].round(1).to_string())
best.to_csv('recent_pst_priceband.csv'); bestb.to_csv('recent_brand_priceband.csv')
