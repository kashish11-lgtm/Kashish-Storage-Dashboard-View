import pandas as pd, numpy as np, json, re
d = pd.read_parquet('storage_full_v2.parquet')
AUG='2026-08'
aug = d[d['month']==AUG].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')
F = 30.4/16  # daily-rate monthly-equiv factor for Aug (16 days)

def agg(df):
    gmv=df['gmv_aed'].sum(); gv=df['gv'].sum(); orders=df['orders'].sum(); units=df['units'].sum()
    instock = df['live_days'].sum()/df['days_in_month'].sum()*100 if df['days_in_month'].sum() else 0
    n_skus=df['sku'].nunique(); n_selling=df.loc[df['gmv_aed']>0,'sku'].nunique()
    return dict(
        gmv=round(gmv*F), cvr=round(orders/gv*100,2) if gv else 0, asp=round(gmv/units,2) if units else 0,
        instock=round(instock,1), skus=int(n_skus), selling=int(n_selling),
        sellpct=round(n_selling/n_skus*100,1) if n_skus else 0
    )

# ---- Level 1: PT ----
pts = sorted(aug['pt'].unique())
L1 = []
for pt in pts:
    L1.append({'id':pt, 'name':pt.replace('_',' ').title(), **agg(aug[aug['pt']==pt])})

# ---- Level 2: PT -> PST (all subcats) ----
L2 = {}
for pt in pts:
    rows=[]
    sub = aug[aug['pt']==pt]
    for pst in sorted(sub['pst'].unique()):
        s = sub[sub['pst']==pst]
        if s['gmv_aed'].sum()==0 and s['sku'].nunique()<3: continue
        rows.append({'id':pst, 'name':pst.replace('_',' ').title(), 'nbrands': int(s['brand'].nunique()), **agg(s)})
    rows.sort(key=lambda r:-r['gmv'])
    L2[pt]=rows

# ---- Level 3: PST -> Brand (top 30) ----
L3 = {}
for pt in pts:
    sub_pt = aug[aug['pt']==pt]
    for pst in sub_pt['pst'].unique():
        s = sub_pt[sub_pt['pst']==pst]
        rows=[]
        for br, g in s.groupby('brand'):
            if g['gmv_aed'].sum()==0: continue
            rows.append({'id':br, 'name':br, **agg(g)})
        rows.sort(key=lambda r:-r['gmv'])
        L3[f"{pt}|{pst}"]=rows[:30]

# ---- Level 4: PST+Brand -> SKU (top 10) ----
L4 = {}
def clean_name(s):
    s = re.sub(r'\s+',' ', str(s)).strip()
    return s[:70]+'…' if len(s)>70 else s

for key, brands in L3.items():
    pt, pst = key.split('|')
    s = aug[(aug['pt']==pt)&(aug['pst']==pst)]
    for b in brands:
        br = b['id']
        sk = s[s['brand']==br]
        sg = sk.groupby(['sku','product_name']).apply(lambda x: pd.Series({
            'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(),
            'instock': x['live_days'].sum()/x['days_in_month'].sum()*100 if x['days_in_month'].sum() else 0,
            'units': x['units'].sum()
        }), include_groups=False).reset_index()
        sg = sg[sg['gmv']>0].sort_values('gmv', ascending=False).head(10)
        rows=[]
        for _,r in sg.iterrows():
            rows.append({
                'name': clean_name(r['product_name']), 'sid': r['sku'],
                'gmv': round(r['gmv']*F), 'cvr': round(r['orders']/r['gv']*100,1) if r['gv'] else 0,
                'instock': round(r['instock'],0), 'units': int(r['units'])
            })
        if rows: L4[f"{pt}|{pst}|{br}"]=rows

print('L1', len(L1), 'psts total', sum(len(v) for v in L2.values()), 'brand-rows total', sum(len(v) for v in L3.values()), 'sku-groups', len(L4))
OUT = {'pt':L1, 'pst':L2, 'brand':L3, 'sku':L4}
with open('drilldown_data.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
import os
print('file size KB', os.path.getsize('drilldown_data.json')/1024)
