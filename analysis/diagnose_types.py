import pandas as pd, numpy as np, re, json
from collections import Counter

d = pd.read_parquet('storage_full_v2.parquet')
recent = d[d['month'].isin(['2026-06','2026-07','2026-08'])].copy()
brands = set(b.lower() for b in json.load(open('brand_list.json')))

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
liters sq ft dia diameter height width depth long wide deep pack-of count qty quantity net wt
weight gram grams kg lbs oz ounce ounces cell cells vc pp abs pet pvc hdpe led usb dc ac volt
watt hz mah pcslot lot amazon noon uae dubai express fast free shipping delivery guarantee
warranty year years month months day days""".split())

def singularize(t):
    if len(t) > 4 and t.endswith('ies'): return t[:-3] + 'y'
    if len(t) > 4 and t.endswith('ses'): return t[:-2]
    if len(t) > 3 and t.endswith('s') and not t.endswith('ss'): return t[:-1]
    return t

def tokenize(name):
    n = re.sub(r'[^a-z0-9 ]', ' ', str(name).lower())
    toks = [t for t in n.split() if t.isalpha() and len(t) > 2]
    return toks

def clean_tokens(name, pst_words):
    toks = tokenize(name)
    out = []
    for t in toks:
        st = singularize(t)
        if st in STOP or t in STOP: continue
        if st in brands or t in brands: continue
        if st in pst_words: continue
        out.append(st)
    return out

curated_ok = {'storage_box','racks','food_containers','space_saver_bag','closet_clothes_hanger','lunch_box','clothes_rack'}
pst_gmv = recent.groupby('pst')['gmv_aed'].sum().sort_values(ascending=False)
target_psts = [p for p in pst_gmv.index if p not in curated_ok and pst_gmv[p] > 0]

for pst in target_psts:
    x = recent[recent['pst']==pst]
    total_gmv = x['gmv_aed'].sum()
    if total_gmv < 500: continue
    pst_words = set(singularize(w) for w in pst.split('_'))
    # bigram candidates
    bigram_gmv = Counter(); bigram_sku = {}
    unigram_gmv = Counter(); unigram_sku = {}
    for _, r in x.iterrows():
        toks = clean_tokens(r['product_name'], pst_words)
        seen_bi = set(); seen_uni = set()
        for i in range(len(toks)-1):
            bg = toks[i]+' '+toks[i+1]
            if bg not in seen_bi:
                bigram_gmv[bg] += r['gmv_aed']
                bigram_sku.setdefault(bg,set()).add(r['sku'])
                seen_bi.add(bg)
        for t in set(toks):
            if t not in seen_uni:
                unigram_gmv[t] += r['gmv_aed']
                unigram_sku.setdefault(t,set()).add(r['sku'])
                seen_uni.add(t)
    print(f"\n{'='*70}\n{pst}  (GMV {total_gmv:.0f}, {x['sku'].nunique()} SKUs)")
    print("Top bigrams:", [(w, round(g), len(bigram_sku[w])) for w,g in bigram_gmv.most_common(10) if len(bigram_sku[w])>=4])
    print("Top unigrams:", [(w, round(g), len(unigram_sku[w])) for w,g in unigram_gmv.most_common(10) if len(unigram_sku[w])>=4])
    print("Sample names:", x.nlargest(5,'gmv_aed')['product_name'].str.slice(0,70).tolist())
