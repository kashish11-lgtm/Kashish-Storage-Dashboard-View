import pandas as pd, numpy as np
d = pd.read_parquet('storage_full_v2.parquet')
AUG='2026-08'
aug = d[d['month']==AUG].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')

# Category-level funnel waterfall (Aug'26, 16-day, monthly-equiv x30.4/16)
F = 30.4/16
impr = aug['impressions'].sum()*F
gv = aug['gv'].sum()*F
atc = aug['atc'].sum()*F
orders = aug['orders'].sum()*F
gmv = aug['gmv_aed'].sum()*F
print("Category funnel (monthly-equiv):")
print(f"Impressions {impr:,.0f} -> GV {gv:,.0f} (CTR {gv/impr*100:.2f}%) -> ATC {atc:,.0f} (ATC-rate {atc/gv*100:.2f}%) -> Orders {orders:,.0f} (CVR {orders/gv*100:.2f}%) -> GMV {gmv:,.0f} (AOV {gmv/orders:.2f})")

cat_ctr = gv/impr; cat_atcr = atc/gv; cat_cvr = orders/gv; cat_aov = gmv/orders

# per pst: compute each stage vs category benchmark, quantify GMV lost at each stage
pst = aug.groupby('pst').apply(lambda x: pd.Series({
    'impr': x['impressions'].sum(), 'gv': x['gv'].sum(), 'atc': x['atc'].sum(), 'orders': x['orders'].sum(), 'gmv': x['gmv_aed'].sum(),
    'asp': x['gmv_aed'].sum()/x['units'].sum() if x['units'].sum() else 0,
}), include_groups=False)
pst = pst[pst['impr']>20000]
pst['ctr']=pst['gv']/pst['impr']
pst['atcr']=pst['atc']/pst['gv'].replace(0,np.nan)
pst['cvr']=pst['orders']/pst['gv'].replace(0,np.nan)
pst['aov']=pst['gmv']/pst['orders'].replace(0,np.nan)

# GMV loss at CTR stage: if pst reached cat_ctr, how much more GV -> extra orders at pst's own cvr*aov
pst['loss_ctr'] = np.maximum(0,(pst['impr']*cat_ctr - pst['gv'])) * pst['cvr'].fillna(cat_cvr) * pst['aov'].fillna(cat_aov)
# GMV loss at ATC stage: if pst reached cat_atcr (using its own gv), extra atc -> assume proportional extra orders (using atc->order rate)
pst['ord_per_atc'] = pst['orders']/pst['atc'].replace(0,np.nan)
pst['loss_atc'] = np.maximum(0,(pst['gv']*cat_atcr - pst['atc'])) * pst['ord_per_atc'].fillna(pst['cvr']/cat_atcr) * pst['aov'].fillna(cat_aov)
# GMV loss at CVR stage: if pst reached cat_cvr on its own gv
pst['loss_cvr'] = np.maximum(0,(pst['gv']*cat_cvr - pst['orders'])) * pst['aov'].fillna(cat_aov)

for c in ['loss_ctr','loss_atc','loss_cvr']: pst[c]=pst[c]*F
pd.set_option('display.width',200)
print("\nTop 10 subcats by CTR-stage loss (impressions not converting to visits):")
print(pst.sort_values('loss_ctr',ascending=False)[['gmv','ctr','loss_ctr']].head(10).round(0))
print("\nTop 10 subcats by ATC-stage loss (visits not adding to cart):")
print(pst.sort_values('loss_atc',ascending=False)[['gmv','atcr','loss_atc']].head(10).round(0))
print("\nTop 10 subcats by CVR-stage loss (ATC not converting to orders):")
print(pst.sort_values('loss_cvr',ascending=False)[['gmv','cvr','loss_cvr']].head(10).round(0))
pst.to_csv('funnel_waterfall_pst.csv')
