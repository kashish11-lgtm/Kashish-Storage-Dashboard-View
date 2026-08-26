import pandas as pd, numpy as np
full = pd.read_parquet('storage_full.parquet')
JUL,AUG='2026-07','2026-08'
h1_months=['2025-01','2025-02','2025-03','2025-04','2025-05','2025-06']
DAILY_MULT=30.4

def sub_month(df,m):
    d=df[df['month']==m]
    r = d.groupby('pst').apply(lambda x: pd.Series({'gv':x['gv'].sum(),'orders':x['orders'].sum(),'gmv':x['gmv_aed'].sum(),'units':x['units'].sum()}), include_groups=False)
    r['cvr']=r['orders']/r['gv'].replace(0,np.nan)
    r['asp']=r['gmv']/r['units'].replace(0,np.nan)
    return r.fillna(0)

s_aug=sub_month(full,AUG); s_jul=sub_month(full,JUL)
s_h1 = full[full['month'].isin(h1_months)].groupby('pst').apply(lambda x: pd.Series({'gv':x['gv'].sum()/6,'orders':x['orders'].sum()/6,'gmv':x['gmv_aed'].sum()/6,'units':x['units'].sum()/6}), include_groups=False)
s_h1['cvr']=s_h1['orders']/s_h1['gv'].replace(0,np.nan)
s_h1['asp']=s_h1['gmv']/s_h1['units'].replace(0,np.nan)

gv_aug_m = s_aug['gv']/16*DAILY_MULT
opp = pd.DataFrame({'gv_aug_monthly':gv_aug_m,'cvr_aug':s_aug['cvr'],'cvr_jul':s_jul['cvr'],'cvr_h1':s_h1['cvr'],'asp_aug':s_aug['asp'],'gmv_aug_monthly':s_aug['gmv']/16*DAILY_MULT})
opp['opp_vs_jul'] = np.where(opp['cvr_jul']>opp['cvr_aug'], opp['gv_aug_monthly']*(opp['cvr_jul']-opp['cvr_aug'])*opp['asp_aug'], 0)
opp['opp_vs_h1']  = np.where(opp['cvr_h1']>opp['cvr_aug'],  opp['gv_aug_monthly']*(opp['cvr_h1']-opp['cvr_aug'])*opp['asp_aug'], 0)
opp = opp.sort_values('opp_vs_jul', ascending=False)
opp.to_csv('conv_opp_subcat.csv')
pd.set_option('display.width',200)
print(opp[['gmv_aug_monthly','cvr_aug','cvr_jul','cvr_h1','opp_vs_jul','opp_vs_h1']].round(3).head(15))
print("\nTotal monthly conv-opp vs Jul (immediate):", opp['opp_vs_jul'].sum())
print("Total monthly conv-opp vs H1'25 avg (structural):", opp['opp_vs_h1'].sum())
