import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
AUG='2026-08'
aug = d[d['month']==AUG].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')

print("=== RETURNS by PST (Aug'26) ===")
r = aug.groupby('pst').apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'returns':x['returns_gmv_aed'].sum()}), include_groups=False)
r=r[r['gmv']>3000]; r['return_pct']=r['returns']/r['gmv']*100
print(r.sort_values('return_pct',ascending=False).head(10).round(1))

print("\n=== RETURNS by BRAND (Aug'26, gmv>=2000) ===")
rb = aug[~aug['brand'].isin(['unbranded_generic','generic'])].groupby('brand').apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'returns':x['returns_gmv_aed'].sum(),'pst':x['pst'].mode().iloc[0] if len(x['pst'].mode()) else ''}), include_groups=False)
rb=rb[rb['gmv']>=2000]; rb['return_pct']=rb['returns']/rb['gmv']*100
print(rb.sort_values('return_pct',ascending=False).head(12).round(1))

print("\n=== CANCELLATIONS by PST (Aug'26) ===")
c = aug.groupby('pst').apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'cancelled':x['cancelled_gmv_aed'].sum()}), include_groups=False)
c=c[c['gmv']>3000]; c['cancel_pct']=c['cancelled']/c['gmv']*100
print(c.sort_values('cancel_pct',ascending=False).head(10).round(1))

print("\n=== CANCELLATIONS by BRAND (Aug'26, gmv>=2000) ===")
cb = aug[~aug['brand'].isin(['unbranded_generic','generic'])].groupby('brand').apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'cancelled':x['cancelled_gmv_aed'].sum()}), include_groups=False)
cb=cb[cb['gmv']>=2000]; cb['cancel_pct']=cb['cancelled']/cb['gmv']*100
print(cb.sort_values('cancel_pct',ascending=False).head(12).round(1))

r.to_csv('returns_by_pst.csv'); rb.to_csv('returns_by_brand.csv')
c.to_csv('cancel_by_pst.csv'); cb.to_csv('cancel_by_brand.csv')

print("\n=== CANNIBALIZATION CHECK 1: SKU proliferation vs GMV growth, by subcat (Aug26 vs Jul26) ===")
jul = d[d['month']=='2026-07']
def sc(df):
    return df.groupby('pst').apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'n_selling':x.loc[x['gmv_aed']>0,'sku'].nunique()}), include_groups=False)
sa,sj = sc(aug), sc(jul)
cann = pd.DataFrame({'gmv_aug':sa['gmv'],'gmv_jul':sj['gmv'],'nsell_aug':sa['n_selling'],'nsell_jul':sj['n_selling']})
cann['gmv_chg_pct']=(cann['gmv_aug']*1.9-cann['gmv_jul'])/cann['gmv_jul']*100  # normalize aug to jul-equivalent days roughly(x1.9)
cann['nsell_chg_pct']=(cann['nsell_aug']-cann['nsell_jul'])/cann['nsell_jul']*100
cann = cann[cann['gmv_jul']>3000]
print("Subcats where selling-SKU count grew faster than GMV (SKU dilution signal):")
print(cann[cann['nsell_chg_pct']>cann['gmv_chg_pct']].sort_values('nsell_chg_pct',ascending=False).head(10).round(1))

print("\n=== CANNIBALIZATION CHECK 2: brands with many SKUs but low GMV/SKU (traffic-splitting risk) ===")
bb = aug[~aug['brand'].isin(['unbranded_generic','generic'])].groupby(['brand','pst']).apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'n_skus':x['sku'].nunique(),'n_selling':x.loc[x['gmv_aed']>0,'sku'].nunique()}), include_groups=False).reset_index()
bb = bb[bb['n_skus']>=15]
bb['gmv_per_sku']=bb['gmv']/bb['n_skus']
bb['selling_pct']=bb['n_selling']/bb['n_skus']*100
print(bb.sort_values('gmv_per_sku').head(10)[['brand','pst','n_skus','n_selling','selling_pct','gmv','gmv_per_sku']].round(1).to_string())
