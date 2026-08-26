import pandas as pd, numpy as np
full = pd.read_parquet('storage_full.parquet')
AUG='2026-08'
aug = full[full['month']==AUG]

# SKU-level (aug snapshot)
sku = aug.groupby(['sku','product_name','brand','pst']).apply(lambda x: pd.Series({
    'gmv': x['gmv_aed'].sum(), 'gv': x['gv'].sum(), 'orders': x['orders'].sum(), 'units': x['units'].sum(),
    'instock': x['instock_pct'].mean(), 'atc': x['atc'].sum(), 'platform_gmv_loss': x['platform_gmv_loss_aed'].sum(),
    'express_gmv_loss': x['express_gmv_loss_aed'].sum(),
}), include_groups=False).reset_index()
sku['cvr']=sku['orders']/sku['gv'].replace(0,np.nan)
sku['asp']=sku['gmv']/sku['units'].replace(0,np.nan)
sku=sku.fillna(0)
print("Total SKUs:", len(sku), "Selling SKUs:", (sku['gmv']>0).sum())

cat_cvr = aug['orders'].sum()/aug['gv'].sum()
# Hero SKUs: top by GMV, good CVR, good instock
hero = sku[(sku['gmv']>0)].sort_values('gmv', ascending=False).head(15)
print("\n=== HERO SKUs (Top GMV, Aug'26) ===")
print(hero[['product_name','brand','pst','gmv','cvr','instock']].round(3).to_string())

# Conversion Opportunity: high GV, low CVR (below cat avg), gv>=p75 among sku with gv>0
gv_p75 = sku.loc[sku['gv']>0,'gv'].quantile(0.9)
conv_opp = sku[(sku['gv']>=gv_p75) & (sku['cvr']<cat_cvr*0.6)].copy()
conv_opp['opp_gmv'] = conv_opp['gv']*cat_cvr*conv_opp['asp'].replace(0,sku['asp'].median()) - conv_opp['gmv']
conv_opp = conv_opp.sort_values('opp_gmv', ascending=False).head(15)
print(f"\n=== CONVERSION OPPORTUNITY SKUs (GV>=p90={gv_p75:.0f}, CVR<{cat_cvr*0.6*100:.1f}%) ===")
print(conv_opp[['product_name','brand','pst','gv','cvr','asp','opp_gmv']].round(2).to_string())
print("Total conv-opp GMV (16-day, top SKUs universe):", conv_opp['opp_gmv'].sum())

# Stock opportunity: high gv, low instock, real loss field
stock_opp = sku[(sku['platform_gmv_loss']>0) | (sku['express_gmv_loss']>0)].sort_values('platform_gmv_loss', ascending=False).head(15)
print("\n=== STOCK OPPORTUNITY SKUs (by platform_gmv_loss, Aug'26 16-day) ===")
print(stock_opp[['product_name','brand','pst','gmv','instock','platform_gmv_loss','express_gmv_loss']].round(1).to_string())
print("SUM platform_gmv_loss top15:", stock_opp['platform_gmv_loss'].sum(), " full cat total:", sku['platform_gmv_loss'].sum())

# Zero-sales SKUs
zero = sku[sku['gmv']==0]
print(f"\nZero-sales SKUs: {len(zero)} of {len(sku)} ({len(zero)/len(sku)*100:.1f}%)")
print(zero.groupby('pst').size().sort_values(ascending=False).head(10))

# Top10/20 concentration
sku_sorted = sku[sku['gmv']>0].sort_values('gmv', ascending=False)
tot = sku_sorted['gmv'].sum()
print(f"\nTop10 SKU concentration: {sku_sorted['gmv'].head(10).sum()/tot*100:.1f}%")
print(f"Top20 SKU concentration: {sku_sorted['gmv'].head(20).sum()/tot*100:.1f}%")
print(f"Top100 SKU concentration: {sku_sorted['gmv'].head(100).sum()/tot*100:.1f}%")
n_selling = len(sku_sorted)
print(f"Long tail (selling SKUs beyond top 100) count: {n_selling-100}, contributes {100-sku_sorted['gmv'].head(100).sum()/tot*100:.1f}% of GMV")

sku.to_csv('sku_table_aug.csv', index=False)
