import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
days_map = {'2025-07':31,'2025-08':31,'2026-07':31,'2026-08':16}

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

sub_aug26 = sub_agg(d[d['month']=='2026-08'])
sub_aug25 = sub_agg(d[d['month']=='2025-08'])
sub_jul26 = sub_agg(d[d['month']=='2026-07'])

flow=['gmv','units','orders','gv','impressions','atc']
sa26=sub_aug26.copy();
for c in flow: sa26[c]=sub_aug26[c]/16*30.4
sa25=sub_aug25.copy()
for c in flow: sa25[c]=sub_aug25[c]/31*30.4
sj26=sub_jul26.copy()
for c in flow: sj26[c]=sub_jul26[c]/31*30.4

cat_aug26=sa26['gmv'].sum(); cat_aug25=sa25['gmv'].sum()
tbl = pd.DataFrame({
 'gmv_aug26': sa26['gmv'], 'gmv_aug25': sa25['gmv'],
 'share_aug26': sa26['gmv']/cat_aug26*100, 'share_aug25': sa25['gmv']/cat_aug25*100,
 'yoy_growth_pct': (sa26['gmv']-sa25['gmv'])/sa25['gmv'].replace(0,np.nan)*100,
 'abs_yoy_chg': sa26['gmv']-sa25['gmv'],
 'gv_yoy_pct': (sa26['gv']-sa25['gv'])/sa25['gv'].replace(0,np.nan)*100,
 'cvr_aug26': sub_aug26['cvr']*100, 'cvr_aug25': sub_aug25['cvr']*100,
 'cvr_yoy_pp': (sub_aug26['cvr']-sub_aug25['cvr'])*100,
 'cvr_jul26': sub_jul26['cvr']*100,
 'asp_aug26': sub_aug26['asp'], 'asp_aug25': sub_aug25['asp'],
 'asp_yoy_pct': (sub_aug26['asp']-sub_aug25['asp'])/sub_aug25['asp'].replace(0,np.nan)*100,
 'instock_aug26': sub_aug26['instock_wtd'],
 'n_skus_aug26': sub_aug26['n_skus'], 'selling_pct_aug26': sub_aug26['selling_pct'],
})
tbl['contribution_pct']=tbl['abs_yoy_chg']/tbl['abs_yoy_chg'].sum()*100
tbl = tbl.sort_values('gmv_aug26', ascending=False)
tbl.to_csv('subcategory_table_v2_yoy.csv')
pd.set_option('display.max_columns',None); pd.set_option('display.width',230)
print(tbl[['gmv_aug26','share_aug26','yoy_growth_pct','abs_yoy_chg','contribution_pct','cvr_aug26','cvr_yoy_pp','cvr_jul26','asp_aug26','asp_yoy_pct','instock_aug26']].head(20).round(1))
print("\n--- Biggest decliners (abs YoY) ---")
print(tbl.sort_values('abs_yoy_chg')[['gmv_aug26','yoy_growth_pct','abs_yoy_chg','cvr_aug26','cvr_yoy_pp']].head(8).round(1))
