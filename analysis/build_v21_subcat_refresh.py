import pandas as pd, numpy as np, json
d = pd.read_parquet('storage_full_v2.parquet')
F = 30.4 / 31  # Aug'26 is now a full 31-day month, same monthly-equiv convention as everywhere else

aug26 = d[d['month'] == '2026-08'].copy()
aug25 = d[d['month'] == '2025-08'].copy()


def agg(df):
    r = df.groupby('pst').apply(lambda x: pd.Series({
        'pt': x['pt'].mode().iloc[0],
        'gmv': x['gmv_aed'].sum(), 'units': x['units'].sum(), 'orders': x['orders'].sum(),
        'gv': x['gv'].sum(), 'impressions': x['impressions'].sum(), 'search_impressions': x['search_impressions'].sum(),
        'atc': x['atc'].sum(),
        'instock': x['live_days'].sum() / x['days_in_month'].sum() * 100 if x['days_in_month'].sum() else 0,
        'n_skus': x['sku'].nunique(), 'n_selling': x.loc[x['gmv_aed'] > 0, 'sku'].nunique(),
    }), include_groups=False).reset_index()
    r['cvr'] = r['orders'] / r['gv'].replace(0, np.nan) * 100
    r['asp'] = r['gmv'] / r['units'].replace(0, np.nan)
    r['atc_pct'] = r['atc'] / r['gv'].replace(0, np.nan) * 100
    r['si_share'] = r['search_impressions'] / r['impressions'].replace(0, np.nan) * 100
    r['selling_pct'] = r['n_selling'] / r['n_skus'] * 100
    return r.set_index('pst')


a26 = agg(aug26)
a25 = agg(aug25)
cat_gmv26 = a26['gmv'].sum() * F
total_abs_chg = (a26['gmv'] * F - a25['gmv'].reindex(a26.index).fillna(0) * F).sum()

name_map = {
    'storage_box': 'Storage Box', 'racks': 'Racks', 'food_containers': 'Food Containers',
    'space_saver_bag': 'Space Saver Bag', 'closet_clothes_hanger': 'Closet Clothes Hanger',
    'lunch_box': 'Lunch Box', 'clothes_rack': 'Clothes Rack', 'bag': 'Bag',
    'cabinet_drawer_organization': 'Cabinet/Drawer Organization', 'lunch_bag': 'Lunch Bag',
    'foldable_wardrobe': 'Foldable Wardrobe', 'storage_set': 'Storage Set', 'spice_jars': 'Spice Jars',
    'storage_basket': 'Storage Basket', 'closet_organization_systems': 'Closet Organization Systems',
    'hanging_closet_organizer': 'Hanging Closet Organizer', 'storage_bottles': 'Storage Bottles',
    'biscuit_cookie_jar': 'Biscuit Cookie Jar', 'other_storage': 'Other Storage',
    'under_bed_storage': 'Under Bed Storage', 'food_saver': 'Food Saver', 'garage_storage': 'Garage Storage',
    'aluminium_foil': 'Aluminium Foil', 'kitchen_storage_accessories': 'Kitchen Storage Accessories',
    'closet_shelf_divider': 'Closet Shelf Divider', 'outdoor_storage': 'Outdoor Storage',
    'paper_towel_holder': 'Paper Towel Holder', 'dinnerware_stemware_storage': 'Dinnerware Stemware Storage',
    'cooler': 'Cooler', 'cling_film': 'Cling Film', 'sink_sets': 'Sink Sets',
    'countertop_wall_organization': 'Countertop Wall Organization',
    'flatware_utensil_storage': 'Flatware Utensil Storage', 'cereal_dispenser': 'Cereal Dispenser',
    'cube_shelf': 'Cube Shelf', 'bread_box': 'Bread Box', 'food_wrap_dispenser': 'Food Wrap Dispenser',
    'travel_containers': 'Travel Containers', 'egg_holder': 'Egg Holder', 'pods': 'Pods',
    'tool_organizers': 'Tool Organizers', 'clamshells_hinged': 'Clamshells Hinged', 'carton': 'Carton',
    'compost': 'Compost',
}

rows = a26.sort_values('gmv', ascending=False)
subcat_lines = []
extra = {}
for pst, r in rows.iterrows():
    pt = r['pt']
    key = f"{pt}|{pst}"
    gmv26 = r['gmv'] * F
    prev = a25.loc[pst] if pst in a25.index else None
    gmv25 = prev['gmv'] * F if prev is not None else 0
    growth = (gmv26 - gmv25) / gmv25 * 100 if gmv25 else (None if gmv26 == 0 else 'new')
    abschg = gmv26 - gmv25
    contrib = abschg / total_abs_chg * 100 if total_abs_chg else 0
    cvr26 = r['cvr'] if not pd.isna(r['cvr']) else 0
    cvr25 = prev['cvr'] if (prev is not None and not pd.isna(prev['cvr'])) else 0
    asp26 = r['asp'] if not pd.isna(r['asp']) else 0
    asp25 = prev['asp'] if (prev is not None and not pd.isna(prev['asp'])) else 0
    aspchg = (asp26 - asp25) / asp25 * 100 if asp25 else 0
    name = name_map.get(pst, pst.replace('_', ' ').title())
    growth_val = round(growth, 1) if isinstance(growth, (int, float)) else 0
    subcat_lines.append(
        f' {{name:"{name}", key:"{key}", gmv:{round(gmv26)}, share:{round(gmv26/cat_gmv26*100,1)}, '
        f'growth:{growth_val}, abs:{round(abschg)}, contrib:{round(contrib,1)}, '
        f'cvr:{round(cvr26,2)},cvrChg:{round(cvr26-cvr25,1)}, asp:{round(asp26,1)},aspChg:{round(aspchg,1)}, '
        f'instock:{round(r["instock"],1)}, nsku:{int(r["n_skus"])}, sellcount:{int(r["n_selling"])}, selling:{round(r["selling_pct"],1)}}},'
    )
    extra[key] = {
        'impressions': round(r['impressions'] * F), 'search_impressions': round(r['search_impressions'] * F),
        'si_share': round(r['si_share'], 1) if not pd.isna(r['si_share']) else 0,
        'gv': round(r['gv'] * F), 'units': round(r['units'] * F), 'atc': round(r['atc'] * F),
        'atc_pct': round(r['atc_pct'], 1) if not pd.isna(r['atc_pct']) else 0,
    }

with open('subcat_js.txt', 'w') as f:
    f.write('const SUBCAT_EXTRA = ' + json.dumps(extra, separators=(',', ':')) + ';\n')
    f.write('const SUBCAT = [\n')
    f.write('\n'.join(subcat_lines))
    f.write('\n];\n')

print(len(rows), 'subcategories written')
print('cat_gmv26 (monthly-equiv):', round(cat_gmv26))
