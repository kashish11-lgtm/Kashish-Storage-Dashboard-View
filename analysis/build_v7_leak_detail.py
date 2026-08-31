import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month']=='2026-08'].copy()
aug['brand']=aug['brand'].fillna('unbranded_generic')
cat_ctr = aug['gv'].sum()/aug['impressions'].sum()
cat_atcr = aug['atc'].sum()/aug['gv'].sum()
cat_cvr = aug['orders'].sum()/aug['gv'].sum()
F = 30.4/16

def brand_agg(pst, min_val, val_col):
    s = aug[aug['pst']==pst]
    g = s.groupby('brand').apply(lambda x: pd.Series({
        'impr': x['impressions'].sum(), 'gv': x['gv'].sum(), 'atc': x['atc'].sum(), 'orders': x['orders'].sum(), 'gmv': x['gmv_aed'].sum(),
    }), include_groups=False)
    g['ctr']=g['gv']/g['impr'].replace(0,np.nan)*100
    g['atcr']=g['atc']/g['gv'].replace(0,np.nan)*100
    g['cvr']=g['orders']/g['gv'].replace(0,np.nan)*100
    g['gmv_mo']=g['gmv']*F
    g = g[g[val_col]>=min_val]
    return g

# CTR detail for the 7 CTR-problem subcats
CTR_SUBS = ['food_containers','closet_clothes_hanger','lunch_box','lunch_bag','cabinet_drawer_organization','storage_set','closet_organization_systems']
ctr_detail = {}
for pst in CTR_SUBS:
    g = brand_agg(pst, 15000, 'impr')
    g = g.sort_values('ctr')
    worst = g.head(4)[['gmv_mo','impr','ctr']].reset_index().to_dict('records')
    best = g.sort_values('ctr',ascending=False).head(3)[['gmv_mo','impr','ctr']].reset_index().to_dict('records')
    ctr_detail[pst] = {'worst': worst, 'best': best, 'cat_avg': round(cat_ctr*100,2)}

# ATC-rate detail for Big 3
ATC_SUBS = ['racks','storage_box','storage_basket']
atc_detail = {}
for pst in ATC_SUBS:
    g = brand_agg(pst, 2000, 'gv')
    g = g.sort_values('atcr')
    worst = g.head(4)[['gmv_mo','gv','atcr']].reset_index().to_dict('records')
    best = g.sort_values('atcr',ascending=False).head(3)[['gmv_mo','gv','atcr']].reset_index().to_dict('records')
    atc_detail[pst] = {'worst': worst, 'best': best, 'cat_avg': round(cat_atcr*100,2)}

# CVR detail for Big3 + lunch_box
CVR_SUBS = ['racks','storage_basket','storage_box','lunch_box']
cvr_detail = {}
for pst in CVR_SUBS:
    g = brand_agg(pst, 2000, 'gv')
    g = g.sort_values('cvr')
    worst = g.head(4)[['gmv_mo','gv','cvr']].reset_index().to_dict('records')
    best = g.sort_values('cvr',ascending=False).head(3)[['gmv_mo','gv','cvr']].reset_index().to_dict('records')
    cvr_detail[pst] = {'worst': worst, 'best': best, 'cat_avg': round(cat_cvr*100,2)}

def clean(o):
    for k in ['worst','best']:
        for r in o[k]:
            r['gmv_mo']=round(r['gmv_mo'])
            for kk in ['impr','gv']:
                if kk in r: r[kk]=int(r[kk])
            for kk in ['ctr','atcr','cvr']:
                if kk in r: r[kk]=round(r[kk],2)
    return o

OUT = {'ctr': {k: clean(v) for k,v in ctr_detail.items()},
       'atc': {k: clean(v) for k,v in atc_detail.items()},
       'cvr': {k: clean(v) for k,v in cvr_detail.items()}}
with open('leak_detail.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
print(json.dumps(OUT['ctr']['food_containers'], indent=2))
print(json.dumps(OUT['atc']['racks'], indent=2))
print(json.dumps(OUT['cvr']['storage_basket'], indent=2))
