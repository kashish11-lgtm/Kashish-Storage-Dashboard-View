import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
AUG26='2026-08'
aug = d[d['month']==AUG26].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')

# full bm table with instock/cancel
bm = aug.groupby('business_model').apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(), 'units': x['units'].sum(),
    'instock': x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
    'express_instock': x['express_live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
    'cancelled': x['cancelled_gmv_aed'].sum(), 'returns': x['returns_gmv_aed'].sum(),
    'platform_loss': x['platform_gmv_loss_aed'].sum(), 'express_loss': x['express_gmv_loss_aed'].sum(),
    'n_skus': x['sku'].nunique(), 'n_brands': x['brand'].nunique(), 'n_sellers': x['partner_id'].nunique(),
}), include_groups=False)
bm['cvr']=bm['orders']/bm['gv']*100
bm['asp']=bm['gmv']/bm['units']
bm['cancel_pct']=bm['cancelled']/bm['gmv']*100
bm['return_pct']=bm['returns']/bm['gmv']*100
bm['share']=bm['gmv']/bm['gmv'].sum()*100
bm['gmv_per_seller']=bm['gmv']/bm['n_sellers']
bm['gmv_per_sku']=bm['gmv']/bm['n_skus']
pd.set_option('display.width',220); pd.set_option('display.max_columns',None)
print(bm[['gmv','share','cvr','asp','instock','express_instock','cancel_pct','return_pct','gmv_per_seller','gmv_per_sku','n_skus','n_sellers']].round(2))
bm.to_csv('bizmodel_table.csv')

FBN_CANCEL = bm.loc['FBN','cancel_pct']
print(f"\nFBN cancel rate benchmark: {FBN_CANCEL:.2f}%")

# per-brand x business_model breakdown, excluding generic
b = aug[aug['brand']!='unbranded_generic'].groupby(['brand','business_model']).apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(),
    'instock': x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
    'cancelled': x['cancelled_gmv_aed'].sum(), 'n_skus': x['sku'].nunique(),
}), include_groups=False).reset_index()
b['cvr']=b['orders']/b['gv'].replace(0,np.nan)*100
b['cancel_pct']=b['cancelled']/b['gmv'].replace(0,np.nan)*100

# brand totals
brand_tot = b.groupby('brand')['gmv'].sum().sort_values(ascending=False)
lowtier = b[b['business_model'].isin(['SBB','DSE'])].groupby('brand').agg(lowtier_gmv=('gmv','sum'), lowtier_cancel=('cancelled','sum')).reset_index()
lowtier['brand_total_gmv']=lowtier['brand'].map(brand_tot)
lowtier['lowtier_share']=lowtier['lowtier_gmv']/lowtier['brand_total_gmv']*100
lowtier = lowtier[(lowtier['brand_total_gmv']>=1000)]  # meaningful brands only
lowtier['recoverable_gmv_if_fbn_cancel'] = np.maximum(0, lowtier['lowtier_cancel'] - lowtier['lowtier_gmv']*(FBN_CANCEL/100))
lowtier = lowtier.sort_values('lowtier_gmv', ascending=False)
print(f"\nBrands (excl. generic) with meaningful GMV (>=AED1000 in Aug'26) sold materially via SBB/DSE:")
print(f"Total brands considered: {len(lowtier)}")
print(lowtier.head(25).round(1).to_string())
print(f"\nTotal recoverable GMV (cancellation-only lens, if SBB/DSE brands matched FBN's {FBN_CANCEL:.1f}% cancel rate): AED {lowtier['recoverable_gmv_if_fbn_cancel'].sum():.0f} (Aug'26, 31-day) -> monthly-equiv AED {lowtier['recoverable_gmv_if_fbn_cancel'].sum()/31*30.4:.0f}")
lowtier.to_csv('bizmodel_brand_migration.csv', index=False)
