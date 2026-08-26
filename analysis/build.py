import pandas as pd, numpy as np, json

pd.set_option('display.width', 200)
storage_pt = ['storage_organization','storage_home_organization']

df1 = pd.read_parquet('df1.parquet')
df2 = pd.read_parquet('df2.parquet')
d1 = df1[df1['pt'].isin(storage_pt)].copy()
d2 = df2[df2['pt'].isin(storage_pt)].copy()
d1['brand'] = d1['brand'].fillna('unbranded_generic')
d2['brand'] = d2['brand'].fillna('unbranded_generic')

full = pd.concat([d1,d2], ignore_index=True)
full.to_parquet('storage_full.parquet')
print("Combined storage rows:", full.shape)
print(full['month'].value_counts().sort_index())

JUL, AUG = '2026-07', '2026-08'
h1_months = ['2025-01','2025-02','2025-03','2025-04','2025-05','2025-06']

def agg_metrics(df):
    g = df.groupby(level=0) if False else None
    out = {}
    out['gmv'] = df['gmv_aed'].sum()
    out['net_gmv'] = df['net_gmv_aed'].sum()
    out['units'] = df['units'].sum()
    out['orders'] = df['orders'].sum()
    out['gv'] = df['gv'].sum()
    out['impressions'] = df['impressions'].sum()
    out['search_impr'] = df['search_impressions'].sum()
    out['nonsearch_impr'] = df['non_search_impressions'].sum()
    out['atc'] = df['atc'].sum()
    out['returns_gmv'] = df['returns_gmv_aed'].sum()
    out['cancelled_gmv'] = df['cancelled_gmv_aed'].sum()
    out['platform_gmv_loss'] = df['platform_gmv_loss_aed'].sum()
    out['express_gmv_loss'] = df['express_gmv_loss_aed'].sum()
    out['coupon_revenue'] = df['coupon_revenue_aed'].sum()
    # weighted instock: weight by gv (demand-weighted) 
    out['instock_wtd'] = np.average(df['instock_pct'], weights=df['gv'].replace(0,np.nan).fillna(0)+1e-9) if df['gv'].sum()>0 else df['instock_pct'].mean()
    out['instock_simple'] = df['instock_pct'].mean()
    out['n_skus'] = df['sku'].nunique()
    out['n_selling_skus'] = df.loc[df['gmv_aed']>0,'sku'].nunique()
    out['asp'] = out['gmv']/out['units'] if out['units'] else 0
    out['cvr'] = out['orders']/out['gv'] if out['gv'] else 0
    out['ctr'] = out['gv']/out['impressions'] if out['impressions'] else 0
    out['atc_rate'] = out['atc']/out['gv'] if out['gv'] else 0
    return out

def by_month(df, m):
    return agg_metrics(df[df['month']==m])

cat_jul = by_month(full, JUL)
cat_aug = by_month(full, AUG)
h1_by_month = {m: by_month(full,m) for m in h1_months}
h1_avg = {}
keys = cat_jul.keys()
for k in ['gmv','net_gmv','units','orders','gv','impressions','search_impr','nonsearch_impr','atc','returns_gmv','cancelled_gmv','platform_gmv_loss','express_gmv_loss','coupon_revenue']:
    h1_avg[k] = np.mean([h1_by_month[m][k] for m in h1_months])
h1_avg['n_skus'] = np.mean([h1_by_month[m]['n_skus'] for m in h1_months])
h1_avg['n_selling_skus'] = np.mean([h1_by_month[m]['n_selling_skus'] for m in h1_months])
h1_avg['instock_wtd'] = np.mean([h1_by_month[m]['instock_wtd'] for m in h1_months])
h1_avg['asp'] = h1_avg['gmv']/h1_avg['units']
h1_avg['cvr'] = h1_avg['orders']/h1_avg['gv']
h1_avg['ctr'] = h1_avg['gv']/h1_avg['impressions']
h1_avg['atc_rate'] = h1_avg['atc']/h1_avg['gv']

days = {'2026-07':31,'2026-08':16}
for m in h1_months: days[m]=None

print(json.dumps({'jul':cat_jul,'aug':cat_aug,'h1_avg':h1_avg}, indent=2, default=str))

print("\n\n=== DAILY RUN-RATE NORMALIZED CATEGORY HEALTH ===")
H1_DAYS = 31+28+31+30+31+30
flow_keys = ['gmv','net_gmv','units','orders','gv','impressions','search_impr','nonsearch_impr','atc',
             'returns_gmv','cancelled_gmv','platform_gmv_loss','express_gmv_loss','coupon_revenue']

h1_total = {k: h1_avg[k]*6 for k in flow_keys}  # since h1_avg[k] was mean of 6 months -> total = *6
def daily(d_metric_dict, ndays):
    return {k: d_metric_dict[k]/ndays for k in flow_keys}

jul_daily = daily(cat_jul, 31)
aug_daily = daily(cat_aug, 16)
h1_daily  = daily(h1_total, H1_DAYS)

def ratios(m):
    gmv=m['gmv']; units=m['units']; orders=m['orders']; gv=m['gv']; impr=m['impressions']; atc=m['atc']
    return dict(asp=gmv/units if units else 0, cvr=orders/gv if gv else 0, ctr=gv/impr if impr else 0,
                atc_rate=atc/gv if gv else 0)

for label,dd in [('Jul26',jul_daily),('Aug26',aug_daily),('H1\'25 avg',h1_daily)]:
    r = ratios(dd)
    print(label, {k:round(v,2) for k,v in dd.items()}, {k:round(v,4) for k,v in r.items()})

cat_health = {
  'jul26': {**jul_daily, **ratios(jul_daily), 'instock': cat_jul['instock_wtd'], 'n_skus':cat_jul['n_skus'],'n_selling':cat_jul['n_selling_skus']},
  'aug26': {**aug_daily, **ratios(aug_daily), 'instock': cat_aug['instock_wtd'], 'n_skus':cat_aug['n_skus'],'n_selling':cat_aug['n_selling_skus']},
  'h1_25_avg': {**h1_daily, **ratios(h1_daily), 'instock': h1_avg['instock_wtd'], 'n_skus':h1_avg['n_skus'],'n_selling':h1_avg['n_selling_skus']},
}
with open('cat_health.json','w') as f:
    json.dump(cat_health, f, indent=2, default=float)

def pct(a,b):
    return (a-b)/b*100 if b else float('nan')

print("\nMoM (Aug vs Jul), daily-rate basis:")
for k in ['gmv','units','orders','gv','impressions','atc']:
    print(f"  {k}: {pct(aug_daily[k], jul_daily[k]):.1f}%")
print("  cvr chg (pp):", (ratios(aug_daily)['cvr']-ratios(jul_daily)['cvr'])*100)
print("  ctr chg (pp):", (ratios(aug_daily)['ctr']-ratios(jul_daily)['ctr'])*100)
print("  asp chg %:", pct(ratios(aug_daily)['asp'], ratios(jul_daily)['asp']))
print("  instock chg (pp):", cat_aug['instock_wtd']-cat_jul['instock_wtd'])

print("\nvs H1'25 avg baseline (Aug26 daily vs H1'25 daily):")
for k in ['gmv','units','orders','gv','impressions','atc']:
    print(f"  {k}: {pct(aug_daily[k], h1_daily[k]):.1f}%")
print("  cvr chg (pp):", (ratios(aug_daily)['cvr']-ratios(h1_daily)['cvr'])*100)
print("  asp chg %:", pct(ratios(aug_daily)['asp'], ratios(h1_daily)['asp']))
print("  instock chg (pp):", cat_aug['instock_wtd']-h1_avg['instock_wtd'])

print("\n\n=== GMV DECOMPOSITION (GMV = GV x CVR x ASP), sequential GV->CVR->ASP ===")
def decompose(d0, d1):
    gv0,gv1 = d0['gv'], d1['gv']
    r0,r1 = ratios(d0), ratios(d1)
    cvr0,cvr1 = r0['cvr'], r1['cvr']
    asp0,asp1 = r0['asp'], r1['asp']
    gmv0,gmv1 = d0['gmv'], d1['gmv']
    traffic_eff = (gv1-gv0)*cvr0*asp0
    conv_eff    = gv1*(cvr1-cvr0)*asp0
    asp_eff     = gv1*cvr1*(asp1-asp0)
    total = traffic_eff+conv_eff+asp_eff
    actual = gmv1-gmv0
    return dict(traffic_eff=traffic_eff, conv_eff=conv_eff, asp_eff=asp_eff, total_check=total, actual_delta=actual)

mom_decomp = decompose(jul_daily, aug_daily)
print("MoM (per day, AED):", {k:round(v,0) for k,v in mom_decomp.items()})
base_decomp = decompose(h1_daily, aug_daily)
print("vs H1'25 baseline (per day, AED):", {k:round(v,0) for k,v in base_decomp.items()})

# share of total delta
for label,dd in [('MoM',mom_decomp),('vs H1base',base_decomp)]:
    tot = dd['actual_delta']
    print(label, 'shares:', {k: round(dd[k]/tot*100,1) for k in ['traffic_eff','conv_eff','asp_eff']})

with open('decomp.json','w') as f:
    json.dump({'mom':mom_decomp,'baseline':base_decomp}, f, indent=2, default=float)

print("\n\n=== CORRECTED DECOMP: GMV = GV x CVR x AOV (AOV=GMV/Orders, exact identity) ===")
def ratios2(m):
    gmv=m['gmv']; orders=m['orders']; gv=m['gv']; units=m['units']
    return dict(aov=gmv/orders if orders else 0, cvr=orders/gv if gv else 0, upo=units/orders if orders else 0, asp_true=gmv/units if units else 0)

def decompose2(d0,d1):
    gv0,gv1=d0['gv'],d1['gv']
    r0,r1=ratios2(d0),ratios2(d1)
    cvr0,cvr1=r0['cvr'],r1['cvr']
    aov0,aov1=r0['aov'],r1['aov']
    traffic_eff=(gv1-gv0)*cvr0*aov0
    conv_eff=gv1*(cvr1-cvr0)*aov0
    aov_eff=gv1*cvr1*(aov1-aov0)
    return dict(traffic_eff=traffic_eff,conv_eff=conv_eff,aov_eff=aov_eff, actual=d1['gmv']-d0['gmv'],
                check=traffic_eff+conv_eff+aov_eff)

mom2 = decompose2(jul_daily, aug_daily)
base2 = decompose2(h1_daily, aug_daily)
print("MoM:", {k:round(v,0) for k,v in mom2.items()})
print("Base:", {k:round(v,0) for k,v in base2.items()})
for label,dd in [('MoM',mom2),('Base',base2)]:
    tot=dd['actual']
    print(label,'shares%:',{k:round(dd[k]/tot*100,1) for k in ['traffic_eff','conv_eff','aov_eff']})

r_jul, r_aug, r_h1 = ratios2(jul_daily), ratios2(aug_daily), ratios2(h1_daily)
print('AOV jul/aug/h1:', r_jul['aov'], r_aug['aov'], r_h1['aov'])
print('UPO jul/aug/h1:', r_jul['upo'], r_aug['upo'], r_h1['upo'])
print('ASP_true jul/aug/h1:', r_jul['asp_true'], r_aug['asp_true'], r_h1['asp_true'])

with open('decomp2.json','w') as f:
    json.dump({'mom':mom2,'base':base2,'ratios':{'jul':r_jul,'aug':r_aug,'h1':r_h1}}, f, indent=2, default=float)

print("\n\n=== SUBCATEGORY (pst) ANALYSIS ===")
def sub_agg(df):
    r = df.groupby('pst').apply(lambda x: pd.Series({
        'gmv': x['gmv_aed'].sum(),
        'units': x['units'].sum(),
        'orders': x['orders'].sum(),
        'gv': x['gv'].sum(),
        'impressions': x['impressions'].sum(),
        'atc': x['atc'].sum(),
        'instock_wtd': np.average(x['instock_pct'], weights=(x['gv']+1e-9)),
        'n_skus': x['sku'].nunique(),
        'n_selling': x.loc[x['gmv_aed']>0,'sku'].nunique(),
        'platform_gmv_loss': x['platform_gmv_loss_aed'].sum(),
        'express_gmv_loss': x['express_gmv_loss_aed'].sum(),
        'returns_gmv': x['returns_gmv_aed'].sum(),
        'cancelled_gmv': x['cancelled_gmv_aed'].sum(),
    }), include_groups=False)
    r['asp'] = r['gmv']/r['units'].replace(0,np.nan)
    r['cvr'] = r['orders']/r['gv'].replace(0,np.nan)
    r['ctr'] = r['gv']/r['impressions'].replace(0,np.nan)
    r['atc_rate'] = r['atc']/r['gv'].replace(0,np.nan)
    r['selling_pct'] = r['n_selling']/r['n_skus']*100
    return r.fillna(0)

sub_jul = sub_agg(full[full['month']==JUL])
sub_aug = sub_agg(full[full['month']==AUG])
sub_h1  = sub_agg(full[full['month'].isin(h1_months)])
# normalize h1 to monthly avg (divide flow cols by 6)
flowcols = ['gmv','units','orders','gv','impressions','atc','platform_gmv_loss','express_gmv_loss','returns_gmv','cancelled_gmv']
sub_h1m = sub_h1.copy()
for c in flowcols: sub_h1m[c] = sub_h1m[c]/6
sub_h1m['asp']=sub_h1m['gmv']*6/ (sub_h1['units']).replace(0,np.nan)  # recompute properly: use totals
sub_h1m['asp']=sub_h1['gmv']/sub_h1['units'].replace(0,np.nan)
sub_h1m['cvr']=sub_h1['orders']/sub_h1['gv'].replace(0,np.nan)
sub_h1m['ctr']=sub_h1['gv']/sub_h1['impressions'].replace(0,np.nan)

# daily-normalize jul(31) aug(16) h1m(30.17 avg) for GMV comparability -> use per-day then *30 to show "monthly equivalent"
sub_jul_d = sub_jul.copy(); 
for c in flowcols: sub_jul_d[c]=sub_jul[c]/31*30.4
sub_aug_d = sub_aug.copy()
for c in flowcols: sub_aug_d[c]=sub_aug[c]/16*30.4
sub_h1_d = sub_h1m.copy()  # already ~monthly avg (30.17 days), close enough to 30.4, leave as is

cat_gmv_aug = sub_aug_d['gmv'].sum()
cat_gmv_jul = sub_jul_d['gmv'].sum()
cat_gmv_h1 = sub_h1_d['gmv'].sum()

tbl = pd.DataFrame({
    'gmv_aug': sub_aug_d['gmv'], 'gmv_jul': sub_jul_d['gmv'], 'gmv_h1': sub_h1_d['gmv'],
    'share_aug': sub_aug_d['gmv']/cat_gmv_aug*100,
    'share_h1': sub_h1_d['gmv']/cat_gmv_h1*100,
    'gmv_growth_mom_pct': (sub_aug_d['gmv']-sub_jul_d['gmv'])/sub_jul_d['gmv'].replace(0,np.nan)*100,
    'gmv_growth_vs_h1_pct': (sub_aug_d['gmv']-sub_h1_d['gmv'])/sub_h1_d['gmv'].replace(0,np.nan)*100,
    'abs_gmv_chg_mom': sub_aug_d['gmv']-sub_jul_d['gmv'],
    'abs_gmv_chg_vs_h1': sub_aug_d['gmv']-sub_h1_d['gmv'],
    'gv_growth_vs_h1_pct': (sub_aug_d['gv']-sub_h1_d['gv'])/sub_h1_d['gv'].replace(0,np.nan)*100,
    'cvr_aug': sub_aug['cvr']*100, 'cvr_h1': sub_h1m['cvr']*100,
    'cvr_chg_pp': (sub_aug['cvr']-sub_h1m['cvr'])*100,
    'asp_aug': sub_aug['asp'], 'asp_h1': sub_h1m['asp'],
    'asp_chg_pct': (sub_aug['asp']-sub_h1m['asp'])/sub_h1m['asp'].replace(0,np.nan)*100,
    'instock_aug': sub_aug['instock_wtd'],
    'n_skus_aug': sub_aug['n_skus'], 'n_selling_aug': sub_aug['n_selling'],
    'selling_pct_aug': sub_aug['selling_pct'],
    'gmv_per_sku_aug': sub_aug['gmv']/sub_aug['n_skus'].replace(0,np.nan),
    'ctr_aug': sub_aug['ctr']*100, 'ctr_h1': sub_h1m['ctr']*100,
})
tbl['contribution_to_cat_chg_vs_h1_pct'] = tbl['abs_gmv_chg_vs_h1']/tbl['abs_gmv_chg_vs_h1'].sum()*100
tbl = tbl.sort_values('gmv_aug', ascending=False)
tbl.to_csv('subcategory_table.csv')
pd.set_option('display.max_rows', 60)
print(tbl[['gmv_aug','share_aug','gmv_growth_vs_h1_pct','abs_gmv_chg_vs_h1','cvr_aug','cvr_chg_pp','asp_aug','instock_aug','n_skus_aug','selling_pct_aug']].round(1))
