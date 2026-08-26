import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
AUG='2026-08'
aug = d[d['month']==AUG].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')

cat_ctr = aug['gv'].sum()/aug['impressions'].sum()

# CTR-problem subcats: brand-level CTR breakdown
ctr_subs = ['food_containers','closet_clothes_hanger','lunch_box','lunch_bag','cabinet_drawer_organization','storage_set','closet_organization_systems']
b = aug[aug['pst'].isin(ctr_subs)].groupby(['pst','brand']).apply(lambda x: pd.Series({
    'impr': x['impressions'].sum(), 'gv': x['gv'].sum(), 'gmv': x['gmv_aed'].sum()
}), include_groups=False).reset_index()
b = b[b['impr']>=15000]
b['ctr']=b['gv']/b['impr']*100
print("Worst-CTR brands within CTR-problem subcats (impr>=15K, Aug'26):")
print(b.sort_values('ctr').head(15)[['pst','brand','impr','gv','gmv','ctr']].round(1).to_string())

print("\nBest-CTR brands (for contrast, same subcats):")
print(b.sort_values('ctr',ascending=False).head(8)[['pst','brand','impr','gv','gmv','ctr']].round(1).to_string())
b.to_csv('ctr_brand_detail.csv', index=False)
