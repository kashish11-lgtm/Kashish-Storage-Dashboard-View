import pandas as pd, numpy as np, json, re

d = pd.read_parquet('storage_full_v2.parquet')
d['brand'] = d['brand'].fillna('unbranded_generic')

jul26 = d[d['month']=='2026-07']
jul25 = d[d['month']=='2025-07']

def agg(df):
    g = df.groupby(['pt','pst','brand'])['gmv_aed'].sum()
    return g

g26 = agg(jul26)
g25 = agg(jul25)

idx = g26.index.union(g25.index)
g26 = g26.reindex(idx, fill_value=0)
g25 = g25.reindex(idx, fill_value=0)

OUT = {}
for (pt,pst,brand), gmv26 in g26.items():
    gmv25 = g25.loc[(pt,pst,brand)]
    if gmv26 <= 0 and gmv25 <= 0:
        continue
    key = f"{pt}|{pst}"
    if gmv25 > 0:
        growth = round((gmv26/gmv25 - 1) * 100, 1)
    elif gmv26 > 0:
        growth = None  # new (no base last year) -- flag distinctly in JS
    else:
        continue
    abs_delta = round(gmv26 - gmv25)
    OUT.setdefault(key, {})[brand] = {'growth': growth, 'abs': abs_delta, 'gmv25': round(gmv25), 'gmv26': round(gmv26)}

with open('brand_yoy.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
import os
print('pt|pst keys:', len(OUT), 'total brand-rows:', sum(len(v) for v in OUT.values()))
print('size KB', os.path.getsize('brand_yoy.json')/1024)

# spot check storage_box
sk = 'storage_home_organization|storage_box'
if sk in OUT:
    top = sorted(OUT[sk].items(), key=lambda kv: -kv[1]['gmv26'])[:8]
    for b,v in top:
        print(b, v)
