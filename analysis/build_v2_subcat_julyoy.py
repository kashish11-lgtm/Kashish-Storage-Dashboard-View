import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')

def sub_agg(df):
    r = df.groupby('pst').apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'units': x['units'].sum(), 'orders': x['orders'].sum(),
        'gv': x['gv'].sum(), 'impressions': x['impressions'].sum(), 'atc': x['atc'].sum(),
        'instock_wtd': x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
        'n_skus': x['sku'].nunique(), 'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
    }), include_groups=False)
    r['asp']=r['gmv']/r['units'].replace(0,np.nan)
    r['cvr']=r['orders']/r['gv'].replace(0,np.nan)
    r['ctr']=r['gv']/r['impressions'].replace(0,np.nan)
    r['selling_pct']=r['n_selling']/r['n_skus']*100
    return r.fillna(0)

# clean full-month YoY: Aug26 vs Aug25 (both 31 days -- no daily normalization
# needed). Aug26 is now a full month, so this is the current/most-recent
# comparison, superseding the earlier Jul26-vs-Jul25 workaround that existed
# only because Aug26 used to be a 16-day partial month.
sa26 = sub_agg(d[d['month']=='2026-08'])
sa25 = sub_agg(d[d['month']=='2025-08'])

cat_a26 = sa26['gmv'].sum(); cat_a25=sa25['gmv'].sum()
tbl = pd.DataFrame({
 'gmv_aug26': sa26['gmv'], 'gmv_aug25': sa25['gmv'],
 'share_aug26': sa26['gmv']/cat_a26*100, 'share_aug25': sa25['gmv']/cat_a25*100,
 'yoy_growth_pct': (sa26['gmv']-sa25['gmv'])/sa25['gmv'].replace(0,np.nan)*100,
 'abs_yoy_chg': sa26['gmv']-sa25['gmv'],
 'gv_yoy_pct': (sa26['gv']-sa25['gv'])/sa25['gv'].replace(0,np.nan)*100,
 'cvr_aug26': sa26['cvr']*100, 'cvr_aug25': sa25['cvr']*100, 'cvr_yoy_pp': (sa26['cvr']-sa25['cvr'])*100,
 'asp_aug26': sa26['asp'], 'asp_aug25': sa25['asp'], 'asp_yoy_pct': (sa26['asp']-sa25['asp'])/sa25['asp'].replace(0,np.nan)*100,
 'instock_aug26': sa26['instock_wtd'], 'n_skus_aug26': sa26['n_skus'], 'selling_pct_aug26': sa26['selling_pct'],
})
tbl['contribution_pct']=tbl['abs_yoy_chg']/tbl['abs_yoy_chg'].sum()*100
tbl = tbl.sort_values('gmv_aug26', ascending=False)
tbl.to_csv('subcategory_table_v3_juloy.csv')
pd.set_option('display.max_columns',None); pd.set_option('display.width',230)
print("Top by current GMV (Aug26), with Aug26-vs-Aug25 clean YoY:")
print(tbl[['gmv_aug26','share_aug26','yoy_growth_pct','abs_yoy_chg','contribution_pct','cvr_aug26','cvr_yoy_pp','asp_aug26','asp_yoy_pct','instock_aug26']].head(20).round(1))
print("\nBiggest abs YoY decliners:")
print(tbl.sort_values('abs_yoy_chg')[['gmv_aug26','yoy_growth_pct','abs_yoy_chg','cvr_yoy_pp']].head(8).round(1))
print("\nBiggest abs YoY gainers:")
print(tbl.sort_values('abs_yoy_chg',ascending=False)[['gmv_aug26','yoy_growth_pct','abs_yoy_chg','contribution_pct']].head(12).round(1))
