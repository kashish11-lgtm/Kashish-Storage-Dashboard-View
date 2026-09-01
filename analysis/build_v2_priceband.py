import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
bins=[0,25,50,100,200,400,np.inf]; labels=['<25 AED','25-50 AED','50-100 AED','100-200 AED','200-400 AED','400+ AED']
d['price_band']=pd.cut(d['offer_price_aed'], bins=bins, labels=labels, right=False)

# "Total SKUs" = listed SKUs that were live (live_days>0) at least 1 day in the
# trailing ~60 days -- approximated as the trailing 2 calendar months relative
# to the snapshot (data is SKU-month grain, no day-of-month detail), same
# convention as the price-band heatmap's total-SKU line.
recent_live_skus = {
    '2026-08': set(d[(d['month'].isin(['2026-07','2026-08'])) & (d['live_days']>0)]['sku'].unique()),
    '2025-08': set(d[(d['month'].isin(['2025-07','2025-08'])) & (d['live_days']>0)]['sku'].unique()),
}

def agg(df, live_set=None):
    r = df.groupby('price_band', observed=True).apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'units': x['units'].sum(), 'orders': x['orders'].sum(),
        'gv': x['gv'].sum(), 'instock_wtd': x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
        'n_skus': x['sku'].nunique() if live_set is None else x[x['sku'].isin(live_set)]['sku'].nunique(),
        'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
    }), include_groups=False)
    r['asp']=r['gmv']/r['units'].replace(0,np.nan); r['cvr']=r['orders']/r['gv'].replace(0,np.nan)
    r['selling_pct']=r['n_selling']/r['n_skus']*100
    return r.fillna(0)

# Aug26 vs Aug25 is now the clean full-month YoY basis (Aug26 is a full 31-day
# month), superseding the earlier Jul-vs-Jul workaround.
a26=agg(d[d['month']=='2026-08'], live_set=recent_live_skus['2026-08'])
a25=agg(d[d['month']=='2025-08'], live_set=recent_live_skus['2025-08'])
cat_a26=a26['gmv'].sum(); cat_a25=a25['gmv'].sum()
tbl = pd.DataFrame({
 'share_a26': a26['gmv']/cat_a26*100, 'share_a25': a25['gmv']/cat_a25*100,
 'yoy_pct': (a26['gmv']-a25['gmv'])/a25['gmv'].replace(0,np.nan)*100,
 'gv_yoy_pct': (a26['gv']-a25['gv'])/a25['gv'].replace(0,np.nan)*100,
 'cvr_a26': a26['cvr']*100, 'cvr_a25': a25['cvr']*100, 'cvr_yoy_pp': (a26['cvr']-a25['cvr'])*100,
 'asp_a26': a26['asp'], 'instock_a26': a26['instock_wtd'], 'selling_a26': a26['selling_pct'], 'nsku_a26': a26['n_skus'],
 'nselling_a26': a26['n_selling'],
})
tbl = tbl.reindex(labels)
tbl['contrib'] = (a26['gmv']-a25['gmv'])
tbl['contrib_pct']=tbl['contrib']/tbl['contrib'].sum()*100
print(tbl.round(1))
tbl.to_csv('priceband_v2_yoy.csv')
