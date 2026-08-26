import pandas as pd, numpy as np
full = pd.read_parquet('storage_full.parquet')
AUG='2026-08'
aug = full[full['month']==AUG]

seller = aug.groupby(['partner_id','partner_name']).apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(), 'units': x['units'].sum(),
    'n_skus': x['sku'].nunique(), 'instock': np.average(x['instock_pct'], weights=(x['gv']+1e-9)),
    'cancelled_gmv': x['cancelled_gmv_aed'].sum(), 'returns_gmv': x['returns_gmv_aed'].sum(),
    'n_brands': x['brand'].nunique(), 'business_model': x['business_model'].mode().iloc[0] if len(x['business_model'].mode()) else None,
}), include_groups=False)
seller['cvr']=seller['orders']/seller['gv'].replace(0,np.nan)
seller['cancel_rate']=seller['cancelled_gmv']/seller['gmv'].replace(0,np.nan)*100
seller['return_rate']=seller['returns_gmv']/seller['gmv'].replace(0,np.nan)*100
seller = seller.fillna(0).sort_values('gmv', ascending=False)
tot = seller['gmv'].sum()
seller['share']=seller['gmv']/tot*100
seller['cum_share']=seller['share'].cumsum()
print("Total sellers (partner_id) with any GMV:", (seller['gmv']>0).sum(), " / total rows:", len(seller))
print("Top seller concentration: top1=%.1f%% top5=%.1f%% top10=%.1f%% top20=%.1f%%"%(seller['share'].iloc[0], seller['share'].head(5).sum(), seller['share'].head(10).sum(), seller['share'].head(20).sum()))
pd.set_option('display.width',200)
print(seller.head(15)[['gmv','share','cum_share','cvr','instock','cancel_rate','return_rate','n_skus','n_brands','business_model']].round(2))

# business model level
bm = aug.groupby('business_model').apply(lambda x: pd.Series({'gmv':x['gmv_aed'].sum(),'gv':x['gv'].sum(),'orders':x['orders'].sum(),
   'instock':np.average(x['instock_pct'],weights=x['gv']+1e-9),'cancelled_gmv':x['cancelled_gmv_aed'].sum(),'returns_gmv':x['returns_gmv_aed'].sum()}), include_groups=False)
bm['cvr']=bm['orders']/bm['gv']; bm['share']=bm['gmv']/bm['gmv'].sum()*100
bm['cancel_rate']=bm['cancelled_gmv']/bm['gmv']*100; bm['return_rate']=bm['returns_gmv']/bm['gmv']*100
print("\nBy business_model:")
print(bm.round(2))

seller.to_csv('seller_table_aug.csv')
