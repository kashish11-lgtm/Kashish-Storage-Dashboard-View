
/* ---- interactive explorer (PT -> PST -> Brand -> SKU) ---- */
let drillPath = [];

function drillCurrentLevel(){
  if(drillPath.length===0) return {items: DRILL.pt, kind:'pt', selfStats:null};
  if(drillPath.length===1){
    const pt = drillPath[0];
    const self = DRILL.pt.find(x=>x.id===pt);
    return {items: DRILL.pst[pt] || [], kind:'pst', selfStats:self};
  }
  if(drillPath.length===2){
    const [pt,pst] = drillPath;
    const self = (DRILL.pst[pt]||[]).find(x=>x.id===pst);
    return {items: DRILL.brand[pt+"|"+pst] || [], kind:'brand', selfStats:self};
  }
  const [pt,pst,br] = drillPath;
  const self = (DRILL.brand[pt+"|"+pst]||[]).find(x=>x.id===br);
  return {items: DRILL.sku[pt+"|"+pst+"|"+br] || [], kind:'sku', selfStats:self};
}
function drillLabelAt(i){
  if(i===0) return (DRILL.pt.find(x=>x.id===drillPath[0])||{}).name || drillPath[0];
  if(i===1) return ((DRILL.pst[drillPath[0]]||[]).find(x=>x.id===drillPath[1])||{}).name || drillPath[1];
  return ((DRILL.brand[drillPath[0]+"|"+drillPath[1]]||[]).find(x=>x.id===drillPath[2])||{}).name || drillPath[2];
}
function renderDrillCrumb(){
  const labels = ["Storage & Organisers"];
  for(let i=0;i<drillPath.length;i++) labels.push(drillLabelAt(i));
  const el = document.getElementById('drill-crumb');
  el.innerHTML = labels.map((lbl,i)=>{
    const isLast = i===labels.length-1;
    const sep = i>0 ? '<span class="sep">›</span>' : '';
    return sep + `<button class="${isLast?'current':''}" data-idx="${i}">${esc(lbl)}</button>`;
  }).join('');
  el.querySelectorAll('button').forEach(btn=>{
    btn.addEventListener('click', ()=>{ drillPath = drillPath.slice(0, parseInt(btn.dataset.idx)); renderDrillAll(); });
  });
}
function renderDrillKPIs(selfStats){
  const el = document.getElementById('drill-kpis');
  if(!selfStats){ el.innerHTML=''; el.style.display='none'; return; }
  el.style.display='';
  const rows = [
    ['GMV/mo', fmtAED(selfStats.gmv)],
    ['CVR', selfStats.cvr.toFixed(1)+'%'],
    ['ASP', 'AED '+selfStats.asp.toFixed(0)],
    ['Instock%', selfStats.instock.toFixed(1)+'%'],
    ['SKUs', selfStats.skus!==undefined ? selfStats.skus.toLocaleString() : '—'],
    ['Selling%', selfStats.sellpct!==undefined ? selfStats.sellpct.toFixed(1)+'%' : '—'],
  ];
  el.innerHTML = rows.map(([k,v])=>`<div class="drill-kpi"><div class="k">${k}</div><div class="v">${v}</div></div>`).join('');
}
function renderDrillList(){
  const {items, kind} = drillCurrentLevel();
  const search = document.getElementById('drill-search').value.trim().toLowerCase();
  const filtered = search ? items.filter(it => (it.name||'').toLowerCase().includes(search)) : items;
  const el = document.getElementById('drill-list');
  if(filtered.length===0){ el.innerHTML = '<div class="drill-empty">No matches at this level.</div>'; return; }
  const max = Math.max(...filtered.map(it=>it.gmv||0), 1);
  const isLeaf = kind==='sku';
  el.innerHTML = filtered.map((it,i)=>{
    const w = Math.max(2, (it.gmv||0)/max*100);
    const metrics = isLeaf
      ? `CVR ${it.cvr.toFixed(1)}% · Instock ${it.instock.toFixed(0)}% · Units/mo ${it.units.toLocaleString()}`
      : `CVR ${it.cvr.toFixed(1)}% · ASP AED ${it.asp.toFixed(0)} · Instock ${it.instock.toFixed(0)}% · ${it.selling}/${it.skus} SKUs selling`;
    return `<button class="drill-row ${isLeaf?'leaf':''}" data-idx="${i}">
      <div class="r1"><span class="name">${esc(it.name)}</span><span class="gmvval">${fmtAED(it.gmv)}${isLeaf?'':' <span class="chev">›</span>'}</span></div>
      <div class="drill-bar"><div class="drill-bar-fill" style="width:${w}%"></div></div>
      <div class="r3">${metrics}</div>
    </button>`;
  }).join('');
  if(!isLeaf){
    el.querySelectorAll('.drill-row').forEach(row=>{
      row.addEventListener('click', ()=>{
        drillPath = [...drillPath, filtered[parseInt(row.dataset.idx)].id];
        document.getElementById('drill-search').value = '';
        renderDrillAll();
      });
    });
  }
}
function renderDrillAll(){
  const {selfStats} = drillCurrentLevel();
  renderDrillCrumb();
  renderDrillKPIs(selfStats);
  renderDrillList();
}
document.getElementById('drill-search').addEventListener('input', renderDrillList);
renderDrillAll();
