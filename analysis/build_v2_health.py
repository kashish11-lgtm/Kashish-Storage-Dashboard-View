import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
days_map = {'2025-01':31,'2025-02':28,'2025-03':31,'2025-04':30,'2025-05':31,'2025-06':30,
            '2025-07':31,'2025-08':31,'2025-09':30,'2025-10':31,'2025-11':30,'2025-12':31,
            '2026-01':31,'2026-02':28,'2026-03':31,'2026-04':30,'2026-05':31,'2026-06':30,
            '2026-07':31,'2026-08':16}

def agg(df):
    o = {}
    o['gmv']=df['gmv_aed'].sum(); o['gv']=df['gv'].sum(); o['orders']=df['orders'].sum()
    o['units']=df['units'].sum(); o['impressions']=df['impressions'].sum(); o['atc']=df['atc'].sum()
    o['instock']=np.average(df['instock_pct'], weights=df['gv']+1e-9)
    o['platform_loss']=df['platform_gmv_loss_aed'].sum(); o['express_loss']=df['express_gmv_loss_aed'].sum()
    return o

def month_daily(m):
    o = agg(d[d['month']==m])
    days = days_map[m]
    flow = ['gmv','gv','orders','units','impressions','atc','platform_loss','express_loss']
    for k in flow: o[k]=o[k]/days
    return o

def ratios(o):
    return dict(asp=o['gmv']/o['units'] if o['units'] else 0, cvr=o['orders']/o['gv'] if o['gv'] else 0,
                aov=o['gmv']/o['orders'] if o['orders'] else 0, ctr=o['gv']/o['impressions'] if o['impressions'] else 0,
                atc_rate=o['atc']/o['gv'] if o['gv'] else 0)

MONTHS = sorted(d['month'].unique())
DAILY = {m: month_daily(m) for m in MONTHS}
for m in MONTHS:
    r = ratios(DAILY[m])
    print(m, 'gmv/day', round(DAILY[m]['gmv'],0), 'monthly-equiv', round(DAILY[m]['gmv']*30.4,0), 'cvr', round(r['cvr']*100,2), 'asp', round(r['asp'],2), 'instock', round(DAILY[m]['instock'] if 'instock' in DAILY[m] else 0,1))

with open('daily_by_month.json','w') as f:
    json.dump(DAILY, f, default=float, indent=2)

def pct(a,b): return (a-b)/b*100 if b else float('nan')

jul26,aug26,jul25,aug25 = DAILY['2026-07'],DAILY['2026-08'],DAILY['2025-07'],DAILY['2025-08']
print("\n=== MoM (Aug26 vs Jul26) ===")
for k in ['gmv','gv','orders','units','impressions']:
    print(k, pct(aug26[k],jul26[k]))
print("\n=== YoY Aug (Aug26 vs Aug25) ===")
for k in ['gmv','gv','orders','units','impressions']:
    print(k, pct(aug26[k],aug25[k]))
print("\n=== YoY Jul (Jul26 vs Jul25) ===")
for k in ['gmv','gv','orders','units','impressions']:
    print(k, pct(jul26[k],jul25[k]))

r_jul26,r_aug26,r_jul25,r_aug25 = ratios(jul26),ratios(aug26),ratios(jul25),ratios(aug25)
print("\nCVR: jul25",r_jul25['cvr']*100,"aug25",r_aug25['cvr']*100,"jul26",r_jul26['cvr']*100,"aug26",r_aug26['cvr']*100)
print("ASP: jul25",r_jul25['asp'],"aug25",r_aug25['asp'],"jul26",r_jul26['asp'],"aug26",r_aug26['asp'])
print("AOV: jul25",r_jul25['aov'],"aug25",r_aug25['aov'],"jul26",r_jul26['aov'],"aug26",r_aug26['aov'])
print("CTR: jul25",r_jul25['ctr']*100,"aug25",r_aug25['ctr']*100,"jul26",r_jul26['ctr']*100,"aug26",r_aug26['ctr']*100)
print("instock: jul25",jul25['instock'],"aug25",aug25['instock'],"jul26",jul26['instock'],"aug26",aug26['instock'])
