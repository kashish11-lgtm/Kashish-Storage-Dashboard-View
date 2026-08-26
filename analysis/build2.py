import pandas as pd, numpy as np
full = pd.read_parquet('storage_full.parquet')
JUL,AUG='2026-07','2026-08'
h1_months = ['2025-01','2025-02','2025-03','2025-04','2025-05','2025-06']

bins = [0,25,50,100,200,400, np.inf]
labels = ['<25 AED','25-50 AED','50-100 AED','100-200 AED','200-400 AED','400+ AED']
full['price_band'] = pd.cut(full['offer_price_aed'], bins=bins, labels=labels, right=False)

def agg(df, gcol):
    r = df.groupby(gcol, observed=True).apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(), 'units': x['units'].sum(), 'orders': x['orders'].sum(),
        'gv': x['gv'].sum(), 'impressions': x['impressions'].sum(),
        'instock_wtd': np.average(x['instock_pct'], weights=(x['gv']+1e-9)),
        'n_skus': x['sku'].nunique(), 'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
    }), include_groups=False)
    r['asp']=r['gmv']/r['units'].replace(0,np.nan)
    r['cvr']=r['orders']/r['gv'].replace(0,np.nan)
    r['ctr']=r['gv']/r['impressions'].replace(0,np.nan)
    r['selling_pct']=r['n_selling']/r['n_skus']*100
    return r.fillna(0)

pb_jul = agg(full[full['month']==JUL],'price_band')
pb_aug = agg(full[full['month']==AUG],'price_band')
pb_h1  = agg(full[full['month'].isin(h1_months)],'price_band')

flowcols=['gmv','units','orders','gv','impressions']
pb_jul_d = pb_jul.copy(); 
for c in flowcols: pb_jul_d[c]=pb_jul[c]/31*30.4
pb_aug_d = pb_aug.copy()
for c in flowcols: pb_aug_d[c]=pb_aug[c]/16*30.4
pb_h1_d = pb_h1.copy()
for c in flowcols: pb_h1_d[c]=pb_h1[c]/6  # 6 months -> monthly avg (~30.17 days, close enough)

cat_aug_gmv=pb_aug_d['gmv'].sum(); cat_h1_gmv=pb_h1_d['gmv'].sum()
res = pd.DataFrame({
 'gmv_aug': pb_aug_d['gmv'], 'gmv_h1': pb_h1_d['gmv'],
 'share_aug': pb_aug_d['gmv']/cat_aug_gmv*100, 'share_h1': pb_h1_d['gmv']/cat_h1_gmv*100,
 'growth_vs_h1_pct': (pb_aug_d['gmv']-pb_h1_d['gmv'])/pb_h1_d['gmv'].replace(0,np.nan)*100,
 'abs_chg_vs_h1': pb_aug_d['gmv']-pb_h1_d['gmv'],
 'gv_growth_vs_h1_pct': (pb_aug_d['gv']-pb_h1_d['gv'])/pb_h1_d['gv'].replace(0,np.nan)*100,
 'cvr_aug': pb_aug['cvr']*100, 'cvr_h1': pb_h1['cvr']*100, 'cvr_chg_pp': (pb_aug['cvr']-pb_h1['cvr'])*100,
 'asp_aug': pb_aug['asp'],
 'instock_aug': pb_aug['instock_wtd'],
 'n_skus_aug': pb_aug['n_skus'], 'selling_pct_aug': pb_aug['selling_pct'],
})
res['contribution_pct'] = res['abs_chg_vs_h1']/res['abs_chg_vs_h1'].sum()*100
res = res.reindex(labels)
res.to_csv('priceband_table.csv')
pd.set_option('display.max_columns', None); pd.set_option('display.width',220)
print(res.round(1))

# Price Band x Subcategory matrix (top 10 subcats by GMV)
top_subs = full[full['month']==AUG].groupby('pst')['gmv_aed'].sum().sort_values(ascending=False).head(10).index.tolist()
mat = full[(full['month']==AUG) & (full['pst'].isin(top_subs))].pivot_table(index='pst', columns='price_band', values='gmv_aed', aggfunc='sum', observed=True).reindex(top_subs)
mat = mat[labels].fillna(0)
mat.to_csv('priceband_x_subcat.csv')
print("\nPrice Band x Subcategory GMV matrix (Aug'26):")
print(mat.round(0))

# SKU counts in matrix too (assortment depth)
mat_n = full[(full['month']==AUG) & (full['pst'].isin(top_subs))].pivot_table(index='pst', columns='price_band', values='sku', aggfunc='nunique', observed=True).reindex(top_subs)
mat_n = mat_n[labels].fillna(0)
mat_n.to_csv('priceband_x_subcat_nsku.csv')
print("\nSKU count matrix:")
print(mat_n)
