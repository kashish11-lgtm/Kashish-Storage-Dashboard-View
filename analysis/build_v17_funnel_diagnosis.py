import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
aug = d[d['month'] == '2026-08'].copy()
jul = d[d['month'] == '2026-07'].copy()
F = 30.4 / 16

# root-cause enrichment for the §05.1 $ opportunity table: for each
# subcategory's dominant loss bucket (from funnel_opportunity.json), work out
# WHY -- vs category benchmark, MoM instock/price movement, assortment
# thinness, and the worst-offending brand -- instead of just a B/C/D label.
opp = json.load(open('funnel_opportunity.json'))
psts = [r['key'].split('|')[1] for r in opp]

impr_c = aug['impressions'].sum() * F
gv_c = aug['gv'].sum() * F
atc_c = aug['atc'].sum() * F
orders_c = aug['orders'].sum() * F
cat_ctr = gv_c / impr_c * 100
cat_atcr = atc_c / gv_c * 100
cat_cvr = orders_c / gv_c * 100
cat_selling_pct = 6615 / 28767 * 100  # matches the Category Health table's Aug'26 figures

recent_live = set(d[(d['month'].isin(['2026-07', '2026-08'])) & (d['live_days'] > 0)]['sku'].unique())


def pst_funnel(df, psts):
    g = df[df['pst'].isin(psts)].groupby('pst').agg(
        impr=('impressions', 'sum'), gv=('gv', 'sum'), atc=('atc', 'sum'), orders=('orders', 'sum'),
        gmv=('gmv_aed', 'sum'), units=('units', 'sum'), live_days=('live_days', 'sum'), days=('days_in_month', 'sum'))
    g['ctr'] = g['gv'] / g['impr'].replace(0, np.nan) * 100
    g['atcr'] = g['atc'] / g['gv'].replace(0, np.nan) * 100
    g['cvr'] = g['orders'] / g['gv'].replace(0, np.nan) * 100
    g['asp'] = g['gmv'] / g['units'].replace(0, np.nan)
    g['instock'] = g['live_days'] / g['days'].replace(0, np.nan) * 100
    return g


a = pst_funnel(aug, psts)
j = pst_funnel(jul, psts)


def assort(df, psts):
    dd = df[df['pst'].isin(psts)]
    tot = dd[dd['sku'].isin(recent_live)].groupby('pst')['sku'].nunique()
    sell = dd[dd['gmv_aed'] > 0].groupby('pst')['sku'].nunique()
    return tot, sell


tot_aug, sell_aug = assort(aug, psts)
tot_jul, sell_jul = assort(jul, psts)

aug_b = aug[aug['pst'].isin(psts)].copy()
aug_b['brand'] = aug_b['brand'].fillna('unbranded_generic')


def brand_table(pst, stage):
    """Top 3 worst-performing brands (meaningful volume only) on the stage
    that's this subcategory's primary problem -- CTR/ATC-rate/CVR/instock."""
    s = aug_b[aug_b['pst'] == pst]
    g = s.groupby('brand').agg(impr=('impressions', 'sum'), gv=('gv', 'sum'), atc=('atc', 'sum'), orders=('orders', 'sum'),
                                gmv=('gmv_aed', 'sum'), live_days=('live_days', 'sum'), days=('days_in_month', 'sum'))
    g = g[g['gmv'] > 300 / F]
    if stage == 'ctr':
        g['metric'] = g['gv'] / g['impr'].replace(0, np.nan) * 100
        g = g[g['impr'] > 1000]
    elif stage == 'atc':
        g['metric'] = g['atc'] / g['gv'].replace(0, np.nan) * 100
        g = g[g['gv'] > 200]
    elif stage == 'cvr':
        g['metric'] = g['orders'] / g['gv'].replace(0, np.nan) * 100
        g = g[g['gv'] > 200]
    else:  # stock
        g['metric'] = g['live_days'] / g['days'].replace(0, np.nan) * 100
        g = g[g['gmv'] > 500 / F]
    if g.empty:
        return []
    g = g.sort_values('metric', ascending=True)
    return [{'brand': br, 'metric': round(row['metric'], 2), 'gmv': round(row['gmv'] * F)}
            for br, row in g.head(3).iterrows()]


results = {}
for r in opp:
    pst = r['key'].split('|')[1]
    row = {}
    row['ctr'] = round(a.loc[pst, 'ctr'], 2) if pst in a.index else 0
    row['atcr'] = round(a.loc[pst, 'atcr'], 2) if pst in a.index else 0
    row['cvr'] = round(a.loc[pst, 'cvr'], 2) if pst in a.index else 0
    row['instock'] = round(a.loc[pst, 'instock'], 1) if pst in a.index else 0
    row['instock_jul'] = round(j.loc[pst, 'instock'], 1) if pst in j.index else 0
    row['instock_chg'] = round(row['instock'] - row['instock_jul'], 1)
    asp_aug = a.loc[pst, 'asp'] if pst in a.index else 0
    asp_jul = j.loc[pst, 'asp'] if pst in j.index else 0
    row['asp_chg_pct'] = round((asp_aug - asp_jul) / asp_jul * 100, 1) if asp_jul else 0
    row['total_sku'] = int(tot_aug.get(pst, 0))
    row['selling_sku'] = int(sell_aug.get(pst, 0))
    row['selling_pct'] = round(row['selling_sku'] / row['total_sku'] * 100, 1) if row['total_sku'] else 0
    row['selling_chg'] = row['selling_sku'] - int(sell_jul.get(pst, 0))

    primary = max([('ctr', r['ctr']), ('conv', r['conv']), ('stock', r['stock'])], key=lambda x: x[1])[0]
    row['primary'] = primary
    stage_key = 'ctr' if primary == 'ctr' else (r['atc_or_cvr'] if primary == 'conv' else 'stock')
    row['stage_key'] = stage_key
    row['worst_brands'] = brand_table(pst, stage_key)

    # root cause: is the B/C stage problem actually a stock or price move in
    # disguise, or thin assortment, before defaulting to listing/execution?
    if primary == 'stock':
        cause = 'Stock'
    elif row['instock_chg'] <= -8 or row['instock'] < 75:
        cause = 'Stock-driven'
    elif row['asp_chg_pct'] >= 15:
        cause = 'Price-driven'
    elif row['selling_pct'] < cat_selling_pct * 0.6:
        cause = 'Thin assortment'
    else:
        cause = 'Execution/listing'
    row['cause'] = cause

    if primary == 'ctr':
        row['metric_label'] = 'CTR'; row['metric_val'] = row['ctr']; row['metric_cat'] = round(cat_ctr, 2)
    elif stage_key == 'atc':
        row['metric_label'] = 'ATC-rate'; row['metric_val'] = row['atcr']; row['metric_cat'] = round(cat_atcr, 2)
    elif stage_key == 'cvr':
        row['metric_label'] = 'CVR'; row['metric_val'] = row['cvr']; row['metric_cat'] = round(cat_cvr, 2)
    else:
        row['metric_label'] = 'Instock%'; row['metric_val'] = row['instock']; row['metric_cat'] = None

    wb = row['worst_brands'][0] if row['worst_brands'] else None
    if cause == 'Stock':
        row['action'] = (f"Fix OOS on {wb['brand']} ({wb['metric']}% instock) — top SKUs below."
                          if wb else "Fix OOS — restock top SKUs below.")
    elif primary == 'ctr':
        row['action'] = (f"Rewrite thumbnail/title for {wb['brand']} ({wb['metric']}% CTR)"
                          if wb else "Search-relevance audit needed.")
    elif stage_key == 'atc':
        row['action'] = (f"Audit PDP image/price badge for {wb['brand']} ({wb['metric']}% ATC-rate)"
                          if wb else "PDP audit needed.")
    else:
        row['action'] = (f"Audit checkout/PDP for {wb['brand']} ({wb['metric']}% CVR)"
                          if wb else "Checkout/PDP audit needed.")
    if cause == 'Price-driven':
        row['action'] = f"ASP +{row['asp_chg_pct']}% MoM — review recent price changes first."
    elif cause == 'Thin assortment':
        row['action'] = f"Selling-SKU rate {row['selling_pct']}% vs {round(cat_selling_pct, 1)}% cat avg — broaden active assortment."

    results[pst] = row

with open('funnel_diag_context.json', 'w') as f:
    json.dump(results, f)

from collections import Counter
print('cat benchmarks: ctr', round(cat_ctr, 2), 'atcr', round(cat_atcr, 2), 'cvr', round(cat_cvr, 2),
      'selling%', round(cat_selling_pct, 1))
print(Counter(r['cause'] for r in results.values()))
