import pandas as pd, numpy as np, re, json, pickle
from collections import Counter

d = pd.read_parquet('storage_full_v2.parquet')
recent = d[d['month'].isin(['2026-06','2026-07','2026-08'])].copy()
DAYS = 30+31+16
F = 30.4/DAYS

# ---- curated rules for the 6 subcategories already hand-reviewed (kept as-is) ----
CURATED = {
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
 # ---- clothes_rack: already reviewed and confirmed good (was auto-generated,
 # frozen here as explicit rules so it can't drift on a future regen) ----
 'clothes_rack': [
   ('Garment Rack', ['garment']),
   ('Metal Clothes Rack', ['metal']),
   ('Double-Rail Rack', ['double']),
   ('Rack w/ Shelf', ['shelf','shelve']),
   ('Closet System Rack', ['closet']),
   ('Rail / Rod Rack', ['rail','rod']),
   ('Other Clothes Rack', []),
 ],
 # ---- round 2: hand-reviewed from real product-title/bigram evidence (not
 # generic single-word auto-clusters) -- see diagnose_types.py output ----
 'cabinet_drawer_organization': [
   ('Vanity / Makeup Organizer', ['vanity','makeup','cosmetic']),
   ('Drawer Divider Tray', ['divider','drawer organizer','drawer tray','desk drawer']),
   ('Utensil Tray', ['utensil']),
   ('Multi-Tier Cabinet Rack', ['tier','cabinet organizer']),
   ('Other Cabinet/Drawer Organizer', []),
 ],
 'bag': [
   ('Digital Luggage Scale', ['luggage scale','baggage scale']),
   ('Tote / Shoulder Bag', ['shoulder','strap','tote','pliage','longchamp']),
   ('Moving / Storage Tote Bag', ['moving','zipper','organization bag']),
   ('Other Bag', []),
 ],
 'lunch_bag': [
   ('Insulated Cooler Bag', ['insulated','cooler','leakproof','leak proof']),
   ('Tote-Style Lunch Bag', ['tote','oxford','shoulder']),
   ('Kids School Lunch Bag', ['school','student','kids']),
   ('Other Lunch Bag', []),
 ],
 'spice_jars': [
   ('Glass Spice Jar (Airtight)', ['glass','airtight']),
   ('Spice Rack / Cabinet Organizer', ['rack','cabinet','drawer']),
   ('Seasoning Shaker / Dispenser', ['shaker','seasoning','funnel','dispenser']),
   ('Other Spice Jars', []),
 ],
 'storage_basket': [
   ('Woven Rope Basket', ['woven','rope','cotton']),
   ('Toy / Book Basket', ['toy','book']),
   ('Fabric / Linen Storage Bin', ['linen','fabric','bin']),
   ('Closet Shelf Basket', ['closet','shelf','wardrobe']),
   ('Other Storage Basket', []),
 ],
 'foldable_wardrobe': [
   ('Portable Wardrobe (w/ Hanging Rod)', ['hanging rod','freestanding','rod']),
   ('Garment Storage Bag (Moisture-Proof)', ['moisture','mold','garment storage']),
   ('Foldable Drawer Wardrobe', ['drawer','cabinet','tier']),
   ('Other Foldable Wardrobe', []),
 ],
 'closet_organization_systems': [
   ('Moving / Storage Tote Bag', ['moving','tote','zipper','carrying','oversized']),
   ('Metal Clip Hanger', ['metal','clip','hanger']),
   ('Wardrobe Organizer', ['wardrobe','hanging']),
   ('Other Closet Organization Systems', []),
 ],
 'storage_set': [
   ('Glass Jar Set (Coffee/Tea/Sugar)', ['jar','glass','coffee','tea','sugar','canister','mason']),
   ('Airtight Cereal / Dry Food Bin', ['cereal','airtight','bin']),
   ('Other Storage Set', []),
 ],
 'hanging_closet_organizer': [
   ('Cube Storage Organizer', ['cube']),
   ('Fabric Hanging Bin', ['fabric','bin','woven']),
   ('Garment Storage Bag', ['garment','dust','zipper','clothing']),
   ('Other Hanging Closet Organizer', []),
 ],
 'storage_bottles': [
   ('Glass Bottle (Airtight)', ['glass','airtight']),
   ('Juice / Oil Bottle', ['juice','oil','drink']),
   ('Water Bottle Rack / Stand', ['water','rack','stand','tier']),
   ('Other Storage Bottles', []),
 ],
 'biscuit_cookie_jar': [
   ('Glass Airtight Jar', ['glass','airtight']),
   ('Overnight Oats Container', ['overnight','oat']),
   ('Candy / Snack Jar', ['candy','snack']),
   ('Other Biscuit/Cookie Jar', []),
 ],
 'other_storage': [
   ('Rolling Drawer Cabinet', ['cabinet','drawer','tier','wheel']),
   ('Foldable Storage Box', ['foldable','box','lid']),
   ('Other', []),
 ],
 'food_saver': [
   ('Vacuum Sealer Bag', ['vacuum','sealer','seal']),
   ('Sous Vide Bag', ['sou vide','sous vide']),
   ('Meal Prep Container', ['meal','prep']),
   ('Other Food Saver', []),
 ],
 'under_bed_storage': [
   ('Clothes / Blanket Storage Bag', ['clothes','clothing','blanket','comforter','zip']),
   ('Under-Bed Storage Bin', ['bin','closet']),
   ('Other Under-Bed Storage', []),
 ],
 'aluminium_foil': [
   ('Aluminium Foil Roll', ['aluminium foil','aluminum foil','foil','embossed']),
   ('Plastic Cling Wrap', ['plastic wrap','cling']),
   ('Other Aluminium Foil', []),
 ],
 'kitchen_storage_accessories': [
   ('Cabinet / Desk Bin Organizer', ['bin','cabinet','desk','multiuse']),
   ('Airtight Glass Jar', ['airtight','glass','jar']),
   ('Refrigerator Organizer', ['refrigerator','fridge']),
   ('Other Kitchen Storage Accessories', []),
 ],
 'garage_storage': [
   ('Foldable Shelving Unit', ['tier','shelf','shelve','shelving']),
   ('Wardrobe / Closet Organizer', ['closet','wardrobe','clothes','clothing','cabinet']),
   ('Tool / Broom Storage', ['tool','broom']),
   ('Other Garage Storage', []),
 ],
 'cling_film': [
   ('Cling Film Roll (w/ Cutter)', ['cutter','wrap','stretch']),
   ('Vacuum Sealer Roll', ['vacuum','sealer']),
   ('Other Cling Film', []),
 ],
 'closet_shelf_divider': [
   ('Expandable Tension Rod / Rack', ['tension','expandable','wardrobe rack']),
   ('Garment Cover / Divider', ['garment','cover','partition','separator']),
   ('Other Closet Shelf Divider', []),
 ],
 'outdoor_storage': [
   ('Outdoor Storage Shed', ['shed','garage','garden']),
   ('Weatherproof Storage Box', ['crate','box']),
   ('Other Outdoor Storage', []),
 ],
 'paper_towel_holder': [
   ('Countertop Roll Holder', ['countertop','weighted base','bamboo']),
   ('Stainless Steel Holder', ['steel','stainless']),
   ('Other Paper Towel Holder', []),
 ],
 'sink_sets': [
   ('Soap Dispenser + Sponge Caddy', ['soap','dispenser','sponge','caddy']),
   ('Sink Organizer Basket', ['basket','organizer']),
   ('Other Sink Sets', []),
 ],
 'countertop_wall_organization': [
   ('Pegboard Wall Organizer Kit', ['pegboard','kit','modular']),
   ('Wall-Mounted Display Shelf', ['shelf','display','hanging']),
   ('Other Countertop/Wall Organization', []),
 ],
 'cooler': [
   ('Hard-Sided Cooler Box', ['cool','insulated','hard cooler']),
   ('Ice Pack / Gel Pack', ['ice pack','gel pack','ice']),
   ('Other Cooler', []),
 ],
 'bread_box': [
   ('Bread Box (Metal/Bamboo)', ['bread box','bin','countertop','counter','metal','bamboo']),
   ('Bakery / Pastry Display Case', ['pastry','bakery','cake','donut','window']),
   ('Other Bread Box', []),
 ],
 'dinnerware_stemware_storage': [
   ('Dish Drying Rack', ['dish drying','drying rack','drainer','dish rack']),
   ('Cutlery / Cup Organizer', ['cutlery','cup','plate','spoon']),
   ('Other Dinnerware/Stemware Storage', []),
 ],
 'cube_shelf': [
   ('Modular Cube Storage Unit', ['cube','unit']),
   ('Display Shelf (Perfume/Cosmetic)', ['perfume','cologne','display']),
   ('Other Cube Shelf', []),
 ],
 'flatware_utensil_storage': [
   ('Dish Drying Rack', ['dish drying','drying rack','drainer','dish rack']),
   ('Cutlery / Silverware Organizer', ['cutlery','spoon','fork','silverware']),
   ('Other Flatware/Utensil Storage', []),
 ],
 'travel_containers': [
   ('Travel Makeup Bag', ['makeup','toiletry']),
   ('Refillable Travel Bottle', ['bottle','oil','refillable','atomizer','atomiser']),
   ('Other Travel Containers', []),
 ],
 'cereal_dispenser': [
   ('Rotating Grain Dispenser', ['grain','rotating','click']),
   ('Airtight Moisture-Proof Container', ['moisture','proof','sealed','airtight']),
   ('Other Cereal Dispenser', []),
 ],
 'food_wrap_dispenser': [
   ('Foil & Cling Wrap Dispenser', ['foil','aluminum','cling','film']),
   ('Paper Towel Dispenser', ['paper','towel']),
   ('Other Food Wrap Dispenser', []),
 ],
 'egg_holder': [
   ('Automatic Rolling Egg Dispenser', ['automatic','rolling','dispenser','refrigerator','fridge']),
   ('Egg Carton / Tray', ['carton','tray']),
   ('Other Egg Holder', []),
 ],
 'pods': [
   ('Coffee Pod / Capsule Organizer', ['coffee','capsule','pod','nespresso']),
   ('Other Pods', []),
 ],
}

STOP = set("""a an the of in on for with and or to at from by is are was were be been being this
that these those it its as into over under above below up down out off again further than then
once here there when where why how all any both each few more most other some such no nor not
only own same so too very can will just should now new premium quality durable heavy duty multi
multipurpose portable non slip design style pro easy use household reusable washable foldable
adjustable universal essential various assorted piece pieces pcs pc pack packs set sets storage
storages organizer organizers organizing organize organized home kitchen box boxes container
containers bag bags rack racks holder holders stand stands large small size sizes color colors
colour colours white black grey gray blue pink red green silver gold beige brown clear transparent
mixed available perfect ideal best great high top ultra super mini mega extra strong sturdy
modern classic elegant stylish practical convenient functional space saving saver room bedroom
bathroom office car indoor outdoor free standing folding collapsible expandable stackable
rolling wheeled wheels handle handles lid lids cover covers cap caps women men kids baby girl
boy unisex xl inch inches cm mm feet foot piece-set combo bundle deal offer edition version
type kind item product products item items number model number's brand made material materials
capacity per total total-capacity approx approximately about really very bpa sqft litre liter
liters sq ft dia diameter approx suitable useful""".split())

# single-word brand names (multi-word/underscored brands are left alone --
# their component words are often ordinary English and too risky to block
# globally) -- excluded so a brand can't leak in as a "type", e.g. Hotpack,
# Falcon, Longchamp, Songmics, Cedargrain all showed up as auto-picked
# "types" before this was added.
BRAND_TOKENS = {b for b in json.load(open('brand_list.json')) if '_' not in b and b.isalpha()}

def singularize(t):
    # crude stemming so "jars"/"jar", "bins"/"bin" etc merge into one bucket
    if len(t) > 4 and t.endswith('ies'): return t[:-3] + 'y'
    if len(t) > 4 and t.endswith('ses'): return t[:-2]
    if len(t) > 3 and t.endswith('s') and not t.endswith('ss'): return t[:-1]
    return t

def tokenize(name):
    n = re.sub(r'[^a-z0-9 ]', ' ', str(name).lower())
    toks = [singularize(t) for t in n.split() if t.isalpha() and len(t) > 2 and t not in STOP and t not in BRAND_TOKENS]
    return toks

def auto_rules(pst, x, max_types=6, min_skus=5, min_share=0.02):
    total_gmv = x['gmv_aed'].sum()
    pst_label = pst.replace('_', ' ').title()
    if total_gmv <= 0:
        return [(f'All {pst_label}', [])]
    # exclude the subcategory's own name-words as "type" labels -- they're
    # near-universal within it by definition and say nothing about type
    name_words = {singularize(w) for w in pst.split('_')}
    cnt_gmv = Counter()
    cnt_sku = {}
    for _, r in x.iterrows():
        toks = set(tokenize(r['product_name'])) - name_words
        for t in toks:
            cnt_gmv[t] += r['gmv_aed']
            cnt_sku.setdefault(t, set()).add(r['sku'])
    candidates = [w for w, g in cnt_gmv.most_common(80)
                  if len(cnt_sku[w]) >= min_skus and g >= min_share * total_gmv]
    # cosmetic fix-ups for a handful of crude-stemming artifacts (shelve->Shelf
    # etc.) so labels read naturally; matching/grouping above is unaffected
    DISPLAY = {'shelve':'Shelf','clothe':'Clothing','knive':'Knife','loave':'Loaf'}
    used_sku = set()
    rules = []
    for w in candidates:
        new_skus = cnt_sku[w] - used_sku
        if len(new_skus) < min_skus:
            continue
        rules.append((DISPLAY.get(w, w.title()), [w]))
        used_sku |= cnt_sku[w]
        if len(rules) >= max_types:
            break
    if not rules:
        return [(f'All {pst_label}', [])]
    rules.append((f'Other {pst_label}', []))
    return rules

def extract_capacity(name):
    m = re.search(r'(\d+(?:\.\d+)?)\s*L\b', str(name), re.I)
    if m:
        v = float(m.group(1))
        if 0.5 <= v <= 500: return v
    m2 = re.search(r'(\d+(?:\.\d+)?)\s*ML\b', str(name), re.I)
    if m2: return float(m2.group(1)) / 1000
    return np.nan

def cap_band(v):
    if pd.isna(v): return None
    if v < 1: return '<1L'
    if v < 5: return '1-5L'
    if v < 20: return '5-20L'
    if v < 40: return '20-40L'
    if v < 60: return '40-60L'
    if v < 80: return '60-80L'
    if v < 120: return '80-120L'
    return '120L+'

CAP_ORDER = ['<1L','1-5L','5-20L','20-40L','40-60L','60-80L','80-120L','120L+']

def clean_name(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    return s[:65] + '…' if len(s) > 65 else s

pst_gmv = recent.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False)
ALL_PSTS = pst_gmv[pst_gmv > 0].index.tolist()
print(f"{len(ALL_PSTS)} subcategories with GMV>0 in Jun-Aug 2026")

PST_LABEL = {p: p.replace('_', ' ').title() for p in ALL_PSTS}
PRODUCT_TYPES = {}      # pst_id -> [{type,gmv,cvr,asp,p25,p75,skus}]
TYPE_CAPACITY = {}      # "pst||type" -> [...]
TYPE_SKUS = {}           # "pst||type" -> [...]
COVERAGE_REPORT = []

for pst in ALL_PSTS:
    x = recent[recent['pst'] == pst].copy()
    rules = CURATED.get(pst) or auto_rules(pst, x)

    def tag(name, rules=rules):
        n = str(name).lower()
        for label, kws in rules:
            if not kws: return label
            if any(k in n for k in kws): return label
        return rules[-1][0]

    x['type'] = x['product_name'].apply(tag)
    x['cap'] = x['product_name'].apply(extract_capacity)
    x['capband'] = x['cap'].apply(cap_band)

    g = x.groupby('type').apply(lambda r: pd.Series({
        'gmv': r['gmv_aed'].sum(), 'gv': r['gv'].sum(), 'orders': r['orders'].sum(),
        'units': r['units'].sum(),
        'p25': r.loc[r['offer_price_aed'] > 0, 'offer_price_aed'].quantile(0.25),
        'p75': r.loc[r['offer_price_aed'] > 0, 'offer_price_aed'].quantile(0.75),
        'n_skus': r['sku'].nunique(),
    }), include_groups=False)
    g['cvr'] = g['orders'] / g['gv'].replace(0, np.nan) * 100
    g['asp'] = g['gmv'] / g['units'].replace(0, np.nan)
    g = g.sort_values('gmv', ascending=False)
    g = g[g['gmv'] > 0]

    rows = []
    for typ, row in g.iterrows():
        rows.append({
            'type': typ,
            'gmv': round(row['gmv'] * F),
            'cvr': round(row['cvr'], 1) if pd.notna(row['cvr']) else 0.0,
            'asp': round(row['asp'], 1) if pd.notna(row['asp']) else 0.0,
            'p25': int(row['p25']) if pd.notna(row['p25']) else 0,
            'p75': int(row['p75']) if pd.notna(row['p75']) else 0,
            'skus': int(row['n_skus']),
        })
    PRODUCT_TYPES[pst] = rows

    for typ in x['type'].unique():
        sub = x[x['type'] == typ]
        if sub['gmv_aed'].sum() <= 0:
            continue
        dk = f"{pst}||{typ}"

        # capacity breakdown
        coverage = sub['cap'].notna().mean()
        n_bands = sub.loc[sub['capband'].notna(), 'capband'].nunique()
        COVERAGE_REPORT.append((dk, round(coverage * 100, 1)))
        if coverage >= 0.12 and n_bands >= 3:
            cg = sub[sub['capband'].notna()].groupby('capband').apply(lambda r: pd.Series({
                'gmv': r['gmv_aed'].sum(), 'gv': r['gv'].sum(), 'orders': r['orders'].sum(),
                'p25': r.loc[r['offer_price_aed'] > 0, 'offer_price_aed'].quantile(0.25),
                'p75': r.loc[r['offer_price_aed'] > 0, 'offer_price_aed'].quantile(0.75),
                'skus': r['sku'].nunique(),
            }), include_groups=False)
            cg['cvr'] = cg['orders'] / cg['gv'].replace(0, np.nan) * 100
            cg = cg.reindex([b for b in CAP_ORDER if b in cg.index])
            crows = []
            for band, crow in cg.iterrows():
                if pd.isna(crow['gmv']) or crow['gmv'] == 0: continue
                crows.append({'band': band, 'gmv': round(crow['gmv'] * F),
                               'cvr': round(crow['cvr'], 1) if pd.notna(crow['cvr']) else 0,
                               'p25': round(crow['p25']) if pd.notna(crow['p25']) else 0,
                               'p75': round(crow['p75']) if pd.notna(crow['p75']) else 0,
                               'skus': int(crow['skus'])})
            if crows:
                TYPE_CAPACITY[dk] = crows

        # SKU fallback (always compute; JS prefers capacity if present)
        sg = sub.groupby(['sku', 'product_name', 'brand']).apply(lambda r: pd.Series({
            'gmv': r['gmv_aed'].sum(), 'gv': r['gv'].sum(), 'orders': r['orders'].sum(),
            'instock': r['live_days'].sum()/r['days_in_month'].sum()*100 if r['days_in_month'].sum() else 0,
            'units': r['units'].sum()
        }), include_groups=False).reset_index()
        sg = sg[sg['gmv'] > 0].sort_values('gmv', ascending=False).head(8)
        srows = []
        for _, r in sg.iterrows():
            srows.append({'n': clean_name(r['product_name']), 'sid': r['sku'],
                          'b': r['brand'] if pd.notna(r['brand']) else 'unbranded_generic',
                          'gmv': round(r['gmv'] * F),
                          'cvr': round(r['orders'] / r['gv'] * 100, 1) if r['gv'] else 0,
                          'asp': round(r['gmv'] / r['units'], 1) if r['units'] else 0,
                          'instock': round(r['instock'], 0)})
        if srows:
            TYPE_SKUS[dk] = srows

    n_types = len(rows)
    label_src = "curated" if pst in CURATED else "auto"
    print(f"{pst:32s} ({label_src:7s}) {n_types} types, total GMV/mo {sum(r['gmv'] for r in rows):>8,}")

OUT = {
    'psts': ALL_PSTS,
    'labels': PST_LABEL,
    'types': PRODUCT_TYPES,
    'capacity': TYPE_CAPACITY,
    'skus': TYPE_SKUS,
}
with open('all_types.json', 'w') as f:
    json.dump(OUT, f, separators=(',', ':'))
import os
print(f"\nWrote all_types.json, size {os.path.getsize('all_types.json')/1024:.1f} KB")
print(f"{len(TYPE_CAPACITY)} (pst,type) pairs have capacity breakdowns; {len(TYPE_SKUS)} have SKU fallback")
