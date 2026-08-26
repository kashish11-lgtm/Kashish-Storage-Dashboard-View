import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
AUG='2026-08'
aug = d[d['month']==AUG].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')

print("=== PT level (Category) ===")
pt = aug.groupby('pt').apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'n_pst': x['pst'].nunique(), 'n_brands': x['brand'].nunique(),
    'n_skus': x['sku'].nunique(), 'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
}), include_groups=False)
pt['selling_pct']=pt['n_selling']/pt['n_skus']*100
print(pt.round(1))

print("\n=== PT x PST assortment depth (Aug'26) ===")
pst = aug.groupby(['pt','pst']).apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'n_brands': x['brand'].nunique(), 'n_skus': x['sku'].nunique(),
    'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
    'gmv_per_sku': x['gmv_aed'].sum()/x['sku'].nunique(),
}), include_groups=False)
pst['selling_pct']=pst['n_selling']/pst['n_skus']*100
pst = pst.sort_values('gmv', ascending=False)
pd.set_option('display.max_rows', 50); pd.set_option('display.width',200)
print(pst.round(1))
pst.to_csv('pt_pst_assortment.csv')
