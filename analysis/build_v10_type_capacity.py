import pandas as pd, numpy as np, json, re

d = pd.read_parquet('storage_full_v2.parquet')
recent = d[d['month'].isin(['2026-06','2026-07','2026-08'])].copy()
DAYS = 30+31+31
F = 30.4/DAYS

RULES = {
 'storage_box': [
   ('Clear Plastic Box (lidded)', ['clear plastic','transparent']),
   ('Cardboard / Moving Box', ['cardboard','carton','corrugated']),
   ('Foldable Fabric Storage Bag', ['foldable','fabric storage','storage bag','wardrobe clothes organizer','blanket storage']),
   ('Rolling Bin w/ Wheels', ['wheel']),
   ('Drawer Organizer', ['drawer']),
   ('Other Storage Box', []),
 ],
 'racks': [
   ('Dish Drying Rack', ['dish ','dish-','dish rack','drying rack']),
   ('Heavy-Duty Shelving Unit', ['heavy duty','shelving','shelf ','tier storage']),
   ('Rotating / Kitchen Rack', ['rotating','kitchen storage rack']),
   ('Other Rack', []),
 ],
 'food_containers': [
   ('Airtight Container Set', ['airtight']),
   ('Glass Container Set', ['glass']),
   ('Cereal / Dry Food Dispenser', ['cereal','dispenser']),
   ('Vacuum / Seal Container', ['vacuum','seal']),
   ('Other Food Container', []),
 ],
 'space_saver_bag': [
   ('Vacuum Compression Bag (w/ pump)', ['vacuum','pump']),
   ('Packing Cube / Travel Bag', ['packing cube','travel']),
   ('Moving / Storage Tote Bag', ['moving','tote']),
   ('Other Space Saver Bag', []),
 ],
 'closet_clothes_hanger': [
   ('Velvet/Flocked Hanger Set', ['velvet','flock']),
   ('Wooden Hanger Set', ['wood']),
   ('Plastic Hanger Set', ['plastic']),
   ('Clip / Skirt Hanger', ['clip','skirt','pant']),
   ('Other Hanger', []),
 ],
 'lunch_box': [
   ('Bento / Compartment Lunch Box', ['bento','compartment']),
   ('Insulated Lunch Bag Set', ['insulated']),
   ('Glass Lunch Container', ['glass']),
   ('Kids Character Lunch Box', ['kids','character','cartoon']),
   ('Other Lunch Box', []),
 ],
}

def extract_capacity(name):
    m = re.search(r'(\d+(?:\.\d+)?)\s*L\b', str(name), re.I)
    if m:
        v = float(m.group(1))
        if 0.5 <= v <= 500: return v
    # also catch ml -> convert, for small containers
    m2 = re.search(r'(\d+(?:\.\d+)?)\s*ML\b', str(name), re.I)
    if m2: return float(m2.group(1))/1000
    return np.nan

def cap_band(v):
    if pd.isna(v): return None
    if v<1: return '<1L'
    if v<5: return '1-5L'
    if v<20: return '5-20L'
    if v<40: return '20-40L'
    if v<60: return '40-60L'
    if v<80: return '60-80L'
    if v<120: return '80-120L'
    return '120L+'

CAP_ORDER = ['<1L','1-5L','5-20L','20-40L','40-60L','60-80L','80-120L','120L+']

OUT = {}
COVERAGE = {}
for pst, rules in RULES.items():
    x = recent[recent['pst']==pst].copy()
    def tag(name):
        n = str(name).lower()
        for label, kws in rules:
            if not kws: return label
            if any(k in n for k in kws): return label
        return rules[-1][0]
    x['type'] = x['product_name'].apply(tag)
    x['cap'] = x['product_name'].apply(extract_capacity)
    x['capband'] = x['cap'].apply(cap_band)
    for typ in x['type'].unique():
        sub = x[x['type']==typ]
        coverage = sub['cap'].notna().mean()
        n_bands = sub.loc[sub['capband'].notna(),'capband'].nunique()
        COVERAGE[f"{pst}||{typ}"] = round(coverage*100,1)
        if coverage>=0.12 and n_bands>=3:
            g = sub[sub['capband'].notna()].groupby('capband').apply(lambda r: pd.Series({
                'gmv': r['gmv_aed'].sum(), 'gv': r['gv'].sum(), 'orders': r['orders'].sum(),
                'p25': r.loc[r['offer_price_aed']>0,'offer_price_aed'].quantile(0.25),
                'p75': r.loc[r['offer_price_aed']>0,'offer_price_aed'].quantile(0.75),
                'skus': r['sku'].nunique(),
            }), include_groups=False)
            g['cvr']=g['orders']/g['gv'].replace(0,np.nan)*100
            g = g.reindex([b for b in CAP_ORDER if b in g.index])
            rows=[]
            for band,row in g.iterrows():
                if pd.isna(row['gmv']) or row['gmv']==0: continue
                rows.append({'band':band,'gmv':round(row['gmv']*F),'cvr':round(row['cvr'],1) if pd.notna(row['cvr']) else 0,
                             'p25':round(row['p25']) if pd.notna(row['p25']) else 0,'p75':round(row['p75']) if pd.notna(row['p75']) else 0,'skus':int(row['skus'])})
            if rows: OUT[f"{pst}||{typ}"]=rows

print("Coverage by (pst,type):")
for k,v in sorted(COVERAGE.items(), key=lambda x:-x[1])[:20]:
    print(f"  {k}: {v}%")
print(f"\n{len(OUT)} (pst,type) pairs have capacity breakdowns")
with open('type_capacity.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
