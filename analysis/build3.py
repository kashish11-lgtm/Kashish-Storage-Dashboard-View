import pandas as pd, numpy as np
full = pd.read_parquet('storage_full.parquet')
AUG='2026-08'
aug = full[full['month']==AUG]

sub = aug.groupby('pst').apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(),
    'impressions': x['impressions'].sum(), 'atc': x['atc'].sum(), 'units': x['units'].sum(),
    'instock_wtd': np.average(x['instock_pct'], weights=(x['gv']+1e-9)),
    'platform_gmv_loss': x['platform_gmv_loss_aed'].sum(),
}), include_groups=False)
sub['ctr']=sub['gv']/sub['impressions']
sub['cvr']=sub['orders']/sub['gv']
sub['atc_rate']=sub['atc']/sub['gv']
sub['asp']=sub['gmv']/sub['units']
sub = sub[sub['gv']>500]  # filter tiny noise subcats

cat_cvr = aug['orders'].sum()/aug['gv'].sum()
cat_ctr = aug['gv'].sum()/aug['impressions'].sum()
print('category CVR', cat_cvr, 'category CTR', cat_ctr)

# benchmark = GMV-weighted 75th pct CVR/CTR among subcats with meaningful volume
cvr_bench = sub['cvr'].quantile(0.75)
ctr_bench = sub['ctr'].quantile(0.75)
instock_bench = 97.5  # reasonable healthy instock target
print('cvr_bench(p75)', cvr_bench, 'ctr_bench(p75)', ctr_bench)

sub['gv_share']=sub['gv']/sub['gv'].sum()*100
med_gv = sub['gv'].median()
med_cvr = sub['cvr'].median()

def classify(row):
    tags=[]
    if row['cvr']>=cat_cvr*1.1 and row['gv']<med_gv:
        tags.append('A: Traffic problem (high CVR, low GV)')
    if row['impressions']>sub['impressions'].median() and row['ctr']<cat_ctr*0.8:
        tags.append('B: CTR problem (impr ok, weak click-through)')
    if row['gv']>=med_gv and row['cvr']<cat_cvr*0.85:
        tags.append('C: Conversion problem (high GV, low CVR)')
    if row['instock_wtd']<96 and row['gv']>=med_gv:
        tags.append('D: Stock problem (demand + weak instock)')
    return tags

sub['problem_tags']=sub.apply(classify, axis=1)
sub_sorted = sub.sort_values('gmv', ascending=False)
pd.set_option('display.max_rows',50); pd.set_option('display.width',220); pd.set_option('display.max_columns',None)
print(sub_sorted[['gmv','gv','cvr','ctr','instock_wtd','platform_gmv_loss','problem_tags']].round(4).to_string())
sub.to_csv('funnel_subcat.csv')

# Quantify GMV impact of conversion problem subcats: potential GMV if CVR raised to cat avg cvr (conservative) holding GV, ASP const
sub['potential_gmv_if_cvr_at_cat'] = sub['gv']*cat_cvr*sub['asp']
sub['conv_opp_gmv'] = np.where(sub['cvr']<cat_cvr, sub['potential_gmv_if_cvr_at_cat']-sub['gmv'], 0)
print("\nConversion-problem GMV opportunity (subcat CVR -> category avg CVR):")
print(sub.sort_values('conv_opp_gmv',ascending=False)[['gmv','cvr','conv_opp_gmv']].head(15).round(0))
print("Total conv opp (subcat level, to cat avg):", sub['conv_opp_gmv'].sum())

# Stock opportunity: instock < bench, potential recapture = platform_gmv_loss + express_gmv_loss (real fields) -- use full including all subcats
loss_all = aug.groupby('pst').apply(lambda x: pd.Series({
   'platform_gmv_loss': x['platform_gmv_loss_aed'].sum(),
   'express_gmv_loss': x['express_gmv_loss_aed'].sum(),
   'gmv': x['gmv_aed'].sum(),
}), include_groups=False).sort_values('platform_gmv_loss', ascending=False)
print("\nTop subcats by platform_gmv_loss (Aug'26, actual field in data):")
print(loss_all.head(15).round(0))
print("\nTOTAL category platform_gmv_loss (Aug'26):", loss_all['platform_gmv_loss'].sum(), " express_gmv_loss:", loss_all['express_gmv_loss'].sum())
