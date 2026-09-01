import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
AUG26='2026-08'
aug = d[d['month']==AUG26].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')
EXCLUDE = {'unbranded_generic','generic'}

bm = pd.read_csv('bizmodel_table.csv', index_col=0)
FBN_CANCEL = bm.loc['FBN','cancel_pct']
FBN_INSTOCK = bm.loc['FBN','instock']
print("Platform/express loss by business model (Aug'26, 31-day):")
loss = aug.groupby('business_model').apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'platform_loss': x['platform_gmv_loss_aed'].sum(), 'express_loss': x['express_gmv_loss_aed'].sum(),
}), include_groups=False)
loss['loss_pct_of_gmv']= loss['platform_loss']/(loss['gmv']+loss['platform_loss'])*100
print(loss.round(1))

# brand x business model, excluding generic tags
b = aug[~aug['brand'].isin(EXCLUDE)].groupby(['brand','business_model']).apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(),
    'instock': x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
    'cancelled': x['cancelled_gmv_aed'].sum(), 'platform_loss': x['platform_gmv_loss_aed'].sum(),
    'n_skus': x['sku'].nunique(),
}), include_groups=False).reset_index()
b['cvr']=b['orders']/b['gv'].replace(0,np.nan)*100
b['cancel_pct']=b['cancelled']/b['gmv'].replace(0,np.nan)*100

brand_tot = b.groupby('brand')['gmv'].sum().sort_values(ascending=False)
lt = b[b['business_model'].isin(['SBB','DSE'])].groupby('brand').agg(
    lowtier_gmv=('gmv','sum'), lowtier_cancel=('cancelled','sum'), lowtier_loss=('platform_loss','sum'),
    lowtier_gv=('gv','sum'), lowtier_orders=('orders','sum'), lowtier_cvr=('cvr','mean')
).reset_index()
lt['brand_total_gmv']=lt['brand'].map(brand_tot)
lt['lowtier_share']=lt['lowtier_gmv']/lt['brand_total_gmv']*100
lt = lt[lt['brand_total_gmv']>=1500]
lt['cancel_recovery'] = np.maximum(0, lt['lowtier_cancel'] - lt['lowtier_gmv']*(FBN_CANCEL/100))
lt['stockout_recovery'] = lt['lowtier_loss']  # already the modeled lost-GMV from OOS at SBB/DSE's own (poor) instock
lt['total_opp_31d'] = lt['cancel_recovery'] + lt['stockout_recovery']
lt['total_opp_monthly'] = lt['total_opp_31d']/31*30.4
lt = lt.sort_values('total_opp_monthly', ascending=False)
pd.set_option('display.width',220)
print(f"\nBrand migration candidates (SBB/DSE-heavy, real brands, >=AED1500 total GMV in Aug'26):")
print(lt.head(20)[['brand','brand_total_gmv','lowtier_gmv','lowtier_share','lowtier_cvr','cancel_recovery','stockout_recovery','total_opp_monthly']].round(1).to_string())
print(f"\nTotal migration opportunity (top list), monthly-equiv: AED {lt['total_opp_monthly'].sum():.0f}")
lt.to_csv('bizmodel_brand_migration_v2.csv', index=False)
