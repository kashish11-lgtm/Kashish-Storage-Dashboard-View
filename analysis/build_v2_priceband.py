import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
bins=[0,25,50,100,200,400,np.inf]; labels=['<25 AED','25-50 AED','50-100 AED','100-200 AED','200-400 AED','400+ AED']
d['price_band']=pd.cut(d['offer_price_aed'], bins=bins, labels=labels, right=False)

def agg(df):
    r = df.groupby('price_band', observed=True).apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'units': x['units'].sum(), 'orders': x['orders'].sum(),
        'gv': x['gv'].sum(), 'instock_wtd': x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
        'n_skus': x['sku'].nunique(), 'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
    }), include_groups=False)
    r['asp']=r['gmv']/r['units'].replace(0,np.nan); r['cvr']=r['orders']/r['gv'].replace(0,np.nan)
    r['selling_pct']=r['n_selling']/r['n_skus']*100
    return r.fillna(0)

j26=agg(d[d['month']=='2026-07']); j25=agg(d[d['month']=='2025-07']); a26=agg(d[d['month']=='2026-08'])
cat_j26=j26['gmv'].sum(); cat_j25=j25['gmv'].sum(); cat_a26=a26['gmv'].sum()
tbl = pd.DataFrame({
 'share_a26': a26['gmv']/cat_a26*100, 'share_j26': j26['gmv']/cat_j26*100, 'share_j25': j25['gmv']/cat_j25*100,
 'yoy_pct': (j26['gmv']-j25['gmv'])/j25['gmv'].replace(0,np.nan)*100,
 'gv_yoy_pct': (j26['gv']-j25['gv'])/j25['gv'].replace(0,np.nan)*100,
 'cvr_a26': a26['cvr']*100, 'cvr_j25': j25['cvr']*100, 'cvr_yoy_pp': (j26['cvr']-j25['cvr'])*100,
 'asp_a26': a26['asp'], 'instock_a26': a26['instock_wtd'], 'selling_a26': a26['selling_pct'], 'nsku_a26': a26['n_skus'],
})
tbl = tbl.reindex(labels)
tbl['contrib'] = (j26['gmv']-j25['gmv'])
tbl['contrib_pct']=tbl['contrib']/tbl['contrib'].sum()*100
print(tbl.round(1))
tbl.to_csv('priceband_v2_yoy.csv')
