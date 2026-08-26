import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
days_map = {'2025-01':31,'2025-02':28,'2025-03':31,'2025-04':30,'2025-05':31,'2025-06':30,
            '2025-07':31,'2025-08':31,'2025-09':30,'2025-10':31,'2025-11':30,'2025-12':31,
            '2026-01':31,'2026-02':28,'2026-03':31,'2026-04':30,'2026-05':31,'2026-06':30,
            '2026-07':31,'2026-08':16}
def agg(df):
    o={}
    o['gmv']=df['gmv_aed'].sum(); o['gv']=df['gv'].sum(); o['orders']=df['orders'].sum()
    o['units']=df['units'].sum(); o['impressions']=df['impressions'].sum(); o['atc']=df['atc'].sum()
    return o
def month_daily(m):
    o=agg(d[d['month']==m]); days=days_map[m]
    for k in o: o[k]=o[k]/days
    return o
def ratios2(o):
    return dict(aov=o['gmv']/o['orders'] if o['orders'] else 0, cvr=o['orders']/o['gv'] if o['gv'] else 0)
def decompose2(d0,d1):
    gv0,gv1=d0['gv'],d1['gv']; r0,r1=ratios2(d0),ratios2(d1)
    cvr0,cvr1=r0['cvr'],r1['cvr']; aov0,aov1=r0['aov'],r1['aov']
    traffic=(gv1-gv0)*cvr0*aov0; conv=gv1*(cvr1-cvr0)*aov0; aov_eff=gv1*cvr1*(aov1-aov0)
    return dict(traffic=traffic,conv=conv,aov=aov_eff, actual=d1['gmv']-d0['gmv'], check=traffic+conv+aov_eff)

jul26,aug26,jul25,aug25 = month_daily('2026-07'),month_daily('2026-08'),month_daily('2025-07'),month_daily('2025-08')
print("MoM (Aug26 vs Jul26), AED/day:", {k:round(v) for k,v in decompose2(jul26,aug26).items()})
print("YoY Aug (Aug26 vs Aug25), AED/day:", {k:round(v) for k,v in decompose2(aug25,aug26).items()})
print("YoY Jul (Jul26 vs Jul25), AED/day:", {k:round(v) for k,v in decompose2(jul25,jul26).items()})

for label,dd in [('MoM',decompose2(jul26,aug26)),('YoY-Aug',decompose2(aug25,aug26)),('YoY-Jul',decompose2(jul25,jul26))]:
    tot=dd['actual']
    print(label,'shares%:',{k:round(dd[k]/tot*100,1) for k in ['traffic','conv','aov']})

# monthly-equiv (x30.4) versions for headline AED figures
print("\nmonthly-equiv AED:")
for label,dd in [('MoM',decompose2(jul26,aug26)),('YoY-Aug',decompose2(aug25,aug26))]:
    print(label, {k: round(v*30.4) for k,v in dd.items()})

print("\nmonthly-equiv AED, YoY-Jul (clean, full month both years):")
dd = decompose2(jul25,jul26)
print({k: round(v*30.4) for k,v in dd.items()})
tot = dd['actual']
print('shares%:', {k: round(dd[k]/tot*100,1) for k in ['traffic','conv','aov']})
