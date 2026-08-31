import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
JUL26,JUL25,AUG26 = '2026-07','2025-07','2026-08'

def agg(df):
    o = {}
    o['gmv']=df['gmv_aed'].sum(); o['gv']=df['gv'].sum(); o['orders']=df['orders'].sum()
    o['units']=df['units'].sum()
    o['instock']=df['live_days'].sum()/df['days_in_month'].sum()*100 if df['days_in_month'].sum() else 0
    o['cancelled']=df['cancelled_gmv_aed'].sum(); o['returns']=df['returns_gmv_aed'].sum()
    o['n_skus']=df['sku'].nunique(); o['n_brands']=df['brand'].nunique(); o['n_sellers']=df['partner_id'].nunique()
    return o

print("=== BUSINESS MODEL LEVEL: current snapshot (Aug'26) ===")
bm_aug = d[d['month']==AUG26].groupby('business_model').apply(lambda x: pd.Series(agg(x)), include_groups=False)
bm_aug['cvr']=bm_aug['orders']/bm_aug['gv']*100
bm_aug['asp']=bm_aug['gmv']/bm_aug['units']
bm_aug['cancel_pct']=bm_aug['cancelled']/bm_aug['gmv']*100
bm_aug['return_pct']=bm_aug['returns']/bm_aug['gmv']*100
bm_aug['share']=bm_aug['gmv']/bm_aug['gmv'].sum()*100
print(bm_aug[['gmv','share','cvr','asp','instock','cancel_pct','return_pct','n_skus','n_brands','n_sellers']].round(2))

print("\n=== BUSINESS MODEL YoY (Jul26 vs Jul25) ===")
bm_j26 = d[d['month']==JUL26].groupby('business_model').apply(lambda x: pd.Series(agg(x)), include_groups=False)
bm_j25 = d[d['month']==JUL25].groupby('business_model').apply(lambda x: pd.Series(agg(x)), include_groups=False)
for bm in bm_j26.index:
    if bm in bm_j25.index:
        g26,g25 = bm_j26.loc[bm,'gmv'], bm_j25.loc[bm,'gmv']
        yoy = (g26-g25)/g25*100 if g25 else np.nan
        cvr26 = bm_j26.loc[bm,'orders']/bm_j26.loc[bm,'gv']*100
        cvr25 = bm_j25.loc[bm,'orders']/bm_j25.loc[bm,'gv']*100
        print(f"{bm}: GMV YoY {yoy:.1f}%  CVR jul25={cvr25:.2f}% -> jul26={cvr26:.2f}%  (Δ{cvr26-cvr25:+.2f}pp)")

print("\n=== SKUs sold via multiple business models simultaneously (Aug'26) ===")
aug = d[d['month']=='2026-08']
sku_bm = aug.groupby('sku')['business_model'].nunique()
multi_bm_skus = sku_bm[sku_bm>1].index
print(f"{len(multi_bm_skus)} SKUs sold via >1 business model in Aug'26 (of {aug['sku'].nunique()} total)")

# same-SKU cross-business-model comparison: pick SKUs with meaningful GV in more than one bm
sub = aug[aug['sku'].isin(multi_bm_skus)]
piv = sub.pivot_table(index='sku', columns='business_model', values=['gv','orders','instock_pct'], aggfunc='sum')
# compute cvr per bm per sku where gv>0
print("\nExample: brand-level view of brands present in BOTH FBN/Retail AND SBB/DSE, with SBB/DSE GMV >= 500 (Aug'26)")
brand_bm = aug.groupby(['brand','business_model']).apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'gv':x['gv'].sum(),'orders':x['orders'].sum(),'instock':x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0}), include_groups=False).reset_index()
brand_bm['cvr']=brand_bm['orders']/brand_bm['gv'].replace(0,np.nan)*100
piv2 = brand_bm.pivot_table(index='brand', columns='business_model', values='gmv', aggfunc='sum').fillna(0)
cand = piv2[( (piv2.get('SBB',0)>=500) | (piv2.get('DSE',0)>=500) ) & ( (piv2.get('FBN',0)>0) | (piv2.get('Retail',0)>0) )]
print(cand.sort_values('SBB' if 'SBB' in cand.columns else 'DSE', ascending=False).head(15).round(0))
