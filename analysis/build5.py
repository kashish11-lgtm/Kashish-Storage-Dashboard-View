import pandas as pd, numpy as np
full = pd.read_parquet('storage_full.parquet')
JUL,AUG='2026-07','2026-08'
h1_months=['2025-01','2025-02','2025-03','2025-04','2025-05','2025-06']
full['brand']=full['brand'].fillna('unbranded_generic')

focus_subs = ['racks','storage_box','storage_basket','food_containers','space_saver_bag','closet_clothes_hanger','lunch_box']
aug = full[full['month']==AUG]
jul = full[full['month']==JUL]
h1 = full[full['month'].isin(h1_months)]

def brand_agg(df, subs):
    d = df[df['pst'].isin(subs)]
    r = d.groupby('brand').apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(), 'units': x['units'].sum(),
        'n_skus': x['sku'].nunique(), 'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
        'instock_wtd': np.average(x['instock_pct'], weights=(x['gv']+1e-9)),
        'returns_gmv': x['returns_gmv_aed'].sum(), 'cancelled_gmv': x['cancelled_gmv_aed'].sum(),
        'platform_gmv_loss': x['platform_gmv_loss_aed'].sum(),
    }), include_groups=False)
    r['cvr']=r['orders']/r['gv'].replace(0,np.nan)
    r['asp']=r['gmv']/r['units'].replace(0,np.nan)
    r['gmv_per_sku']=r['gmv']/r['n_skus']
    r['zero_sales_pct']=(r['n_skus']-r['n_selling'])/r['n_skus']*100
    return r.fillna(0)

for target in ['racks','storage_box','storage_basket']:
    b_aug = brand_agg(aug,[target])
    b_h1  = brand_agg(h1,[target])
    b_h1m = b_h1.copy()
    for c in ['gmv','gv','orders','units']: b_h1m[c]=b_h1m[c]/6
    tot_aug = b_aug['gmv'].sum(); tot_h1=b_h1m['gmv'].sum()
    tbl = pd.DataFrame({
        'gmv_aug': b_aug['gmv']/16*30.4, 'share_aug': b_aug['gmv']/tot_aug*100,
        'gmv_h1': b_h1m['gmv'], 'share_h1': b_h1m['gmv']/tot_h1*100,
        'cvr_aug': b_aug['cvr']*100, 'cvr_h1': b_h1m['orders']/b_h1['gv'].replace(0,np.nan)*100,
        'instock_aug': b_aug['instock_wtd'], 'n_skus': b_aug['n_skus'], 'zero_sales_pct': b_aug['zero_sales_pct'],
        'gmv_per_sku': b_aug['gmv_per_sku'],
    })
    tbl['share_chg_pp']=tbl['share_aug']-tbl['share_h1']
    tbl = tbl.sort_values('gmv_aug', ascending=False).head(10)
    print(f"=== TOP BRANDS in {target} (Aug'26 monthly-equiv) ===")
    pd.set_option('display.width',200)
    print(tbl.round(2))
    print()
