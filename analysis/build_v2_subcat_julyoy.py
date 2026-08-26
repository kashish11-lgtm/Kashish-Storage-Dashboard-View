import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')

def sub_agg(df):
    r = df.groupby('pst').apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'units': x['units'].sum(), 'orders': x['orders'].sum(),
        'gv': x['gv'].sum(), 'impressions': x['impressions'].sum(), 'atc': x['atc'].sum(),
        'instock_wtd': np.average(x['instock_pct'], weights=(x['gv']+1e-9)),
        'n_skus': x['sku'].nunique(), 'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
    }), include_groups=False)
    r['asp']=r['gmv']/r['units'].replace(0,np.nan)
    r['cvr']=r['orders']/r['gv'].replace(0,np.nan)
    r['ctr']=r['gv']/r['impressions'].replace(0,np.nan)
    r['selling_pct']=r['n_selling']/r['n_skus']*100
    return r.fillna(0)

# clean full-month YoY: Jul26 vs Jul25 (both 31 days -- no daily normalization needed)
sj26 = sub_agg(d[d['month']=='2026-07'])
sj25 = sub_agg(d[d['month']=='2025-07'])
sa26 = sub_agg(d[d['month']=='2026-08'])  # for current-state cvr/asp/instock/sku snapshot

cat_j26 = sj26['gmv'].sum(); cat_j25=sj25['gmv'].sum()
tbl = pd.DataFrame({
 'gmv_jul26': sj26['gmv'], 'gmv_jul25': sj25['gmv'],
 'share_jul26': sj26['gmv']/cat_j26*100, 'share_jul25': sj25['gmv']/cat_j25*100,
 'yoy_growth_pct': (sj26['gmv']-sj25['gmv'])/sj25['gmv'].replace(0,np.nan)*100,
 'abs_yoy_chg': sj26['gmv']-sj25['gmv'],
 'gv_yoy_pct': (sj26['gv']-sj25['gv'])/sj25['gv'].replace(0,np.nan)*100,
 'cvr_jul26': sj26['cvr']*100, 'cvr_jul25': sj25['cvr']*100, 'cvr_yoy_pp': (sj26['cvr']-sj25['cvr'])*100,
 'asp_jul26': sj26['asp'], 'asp_jul25': sj25['asp'], 'asp_yoy_pct': (sj26['asp']-sj25['asp'])/sj25['asp'].replace(0,np.nan)*100,
 # current snapshot (aug26) for instock/sku columns since that's "now"
 'instock_aug26': sa26['instock_wtd'], 'n_skus_aug26': sa26['n_skus'], 'selling_pct_aug26': sa26['selling_pct'],
 'gmv_aug26': sa26['gmv']/16*30.4,
})
tbl['contribution_pct']=tbl['abs_yoy_chg']/tbl['abs_yoy_chg'].sum()*100
tbl = tbl.sort_values('gmv_aug26', ascending=False)
tbl.to_csv('subcategory_table_v3_juloy.csv')
pd.set_option('display.max_columns',None); pd.set_option('display.width',230)
print("Top by current GMV (Aug26), with Jul26-vs-Jul25 clean YoY:")
print(tbl[['gmv_aug26','share_jul26','yoy_growth_pct','abs_yoy_chg','contribution_pct','cvr_jul26','cvr_yoy_pp','asp_jul26','asp_yoy_pct','instock_aug26']].head(20).round(1))
print("\nBiggest abs YoY decliners:")
print(tbl.sort_values('abs_yoy_chg')[['gmv_aug26','yoy_growth_pct','abs_yoy_chg','cvr_yoy_pp']].head(8).round(1))
print("\nBiggest abs YoY gainers:")
print(tbl.sort_values('abs_yoy_chg',ascending=False)[['gmv_aug26','yoy_growth_pct','abs_yoy_chg','contribution_pct']].head(12).round(1))
