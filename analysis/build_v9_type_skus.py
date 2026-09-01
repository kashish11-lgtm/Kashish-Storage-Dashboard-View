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
def clean_name(s):
    s = re.sub(r'\s+',' ', str(s)).strip()
    return s[:65]+'…' if len(s)>65 else s

OUT = {}
for pst, rules in RULES.items():
    x = recent[recent['pst']==pst].copy()
    def tag(name):
        n = str(name).lower()
        for label, kws in rules:
            if not kws: return label
            if any(k in n for k in kws): return label
        return rules[-1][0]
    x['type'] = x['product_name'].apply(tag)
    for typ in x['type'].unique():
        sub = x[x['type']==typ]
        sg = sub.groupby(['sku','product_name','brand']).apply(lambda r: pd.Series({
            'gmv': r['gmv_aed'].sum(), 'gv': r['gv'].sum(), 'orders': r['orders'].sum(),
            'instock': r['live_days'].sum()/r['days_in_month'].sum()*100 if r['days_in_month'].sum() else 0,
            'units': r['units'].sum()
        }), include_groups=False).reset_index()
        sg = sg[sg['gmv']>0].sort_values('gmv', ascending=False).head(8)
        rows=[]
        for _,r in sg.iterrows():
            rows.append({'n': clean_name(r['product_name']), 'b': r['brand'] if pd.notna(r['brand']) else 'unbranded_generic',
                         'gmv': round(r['gmv']*F), 'cvr': round(r['orders']/r['gv']*100,1) if r['gv'] else 0, 'instock': round(r['instock'],0)})
        OUT[f"{pst}||{typ}"] = rows

with open('type_sku_detail.json','w') as f:
    json.dump(OUT, f, separators=(',',':'))
import os
print('entries', len(OUT), 'size KB', os.path.getsize('type_sku_detail.json')/1024)
