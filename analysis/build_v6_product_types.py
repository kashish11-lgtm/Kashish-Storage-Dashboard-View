import pandas as pd, numpy as np, re

d = pd.read_parquet('storage_full_v2.parquet')
recent = d[d['month'].isin(['2026-06','2026-07','2026-08'])].copy()

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

out = {}
for pst, rules in RULES.items():
    x = recent[recent['pst']==pst].copy()
    def tag(name):
        n = str(name).lower()
        for label, kws in rules:
            if not kws: return label
            if any(k in n for k in kws): return label
        return rules[-1][0]
    x['type'] = x['product_name'].apply(tag)
    g = x.groupby('type').apply(lambda r: pd.Series({
        'gmv': r['gmv_aed'].sum(), 'gv': r['gv'].sum(), 'orders': r['orders'].sum(),
        'units': r['units'].sum(), 'p25': r.loc[r['offer_price_aed']>0,'offer_price_aed'].quantile(0.25),
        'p75': r.loc[r['offer_price_aed']>0,'offer_price_aed'].quantile(0.75),
        'n_skus': r['sku'].nunique(),
    }), include_groups=False)
    g['cvr']=g['orders']/g['gv'].replace(0,np.nan)*100
    g['asp']=g['gmv']/g['units'].replace(0,np.nan)
    g=g.sort_values('gmv',ascending=False)
    out[pst]=g
    print(f"\n=== {pst} (Jun-Aug'26) ===")
    pd.set_option('display.width',160)
    print(g[['gmv','cvr','asp','p25','p75','n_skus']].round(1))

import pickle
with open('product_types.pkl','wb') as f:
    pickle.dump(out, f)
