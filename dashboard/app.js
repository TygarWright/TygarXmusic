const $ = (id) => document.getElementById(id);
const setStatus = (id, value, detail) => { $(id).textContent = value; if (detail) $(id+'-detail').textContent = detail; };
async function probe(path){ const started=performance.now(); try{ const r=await fetch(path); const data=await r.json(); return {ok:r.ok,data,ms:Math.round(performance.now()-started)} }catch(error){ return {ok:false,error,ms:Math.round(performance.now()-started)} } }
async function refresh(){
  const [health, ready, metrics] = await Promise.all([probe('/healthz'), probe('/readyz'), probe('/metrics')]);
  setStatus('health', health.ok ? 'ONLINE' : 'ERROR', health.ok ? `${health.ms} ms response` : 'Probe failed');
  setStatus('ready', ready.ok ? 'READY' : 'WAITING', ready.ok ? `${ready.ms} ms response` : 'Dependencies unavailable');
  $('overall').textContent = health.ok && ready.ok ? 'Operational' : 'Attention needed'; $('overall').className = 'badge '+(health.ok && ready.ok ? 'good':'bad');
  if(metrics.ok){ $('uptime').textContent = metrics.data.uptime || '—'; $('calls').textContent = metrics.data.active_calls ?? '—'; $('signals').innerHTML = Object.entries(metrics.data).filter(([k])=>!['uptime','active_calls'].includes(k)).map(([k,v])=>`<div class="signal"><span>${k.replaceAll('_',' ')}</span><span>${v}</span></div>`).join(''); }
  $('updated').textContent = `Updated ${new Date().toLocaleTimeString()}`;
}
document.querySelectorAll('.action[data-path]').forEach(b=>b.addEventListener('click',async()=>{const r=await probe(b.dataset.path);b.textContent=r.ok?'✓ '+b.textContent:'× '+b.textContent;setTimeout(()=>b.textContent=b.textContent.slice(2),1200)}));
$('refresh').addEventListener('click',refresh); refresh(); setInterval(refresh,15000);
