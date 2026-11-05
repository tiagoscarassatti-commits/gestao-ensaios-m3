/* ===================== ANÁLISE DE ESTANDE ===================== */
let ES = null, eSub = 'geral', eConf = null, eArr = null, eArrFim = null;
document.addEventListener('mouseup', () => { if (eArr != null && !document.getElementById('eHist').matches(':hover')) eArr = null });
const RUIM = -15, ATENC = -10;
const COR = { r: '#c62828', a: '#e0a100', o: '#B4BD00', p: '#003DA6' };
const st = d => d <= RUIM ? 'r' : d <= ATENC ? 'a' : 'o';
const STN = { r: 'Ruim', a: 'Atenção', o: 'Adequado' };
const pp = d => (d > 0 ? '+' : '') + d.toFixed(1).replace('.', ',') + '%';
const pt = n => n == null ? '–' : Math.round(n).toLocaleString('pt-BR');
const media = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
const semAc = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase();
const difHtml = d => d == null ? '<span class="note">–</span>' : `<span class="dif ${st(d)}">${pp(d)}</span>`;
function dvBar(d) {
  if (d == null) return '';
  const w = Math.min(Math.abs(d), 30) / 30 * 45, c = d < 0 ? COR[st(d)] : COR.p;
  return `<span class="dv">${difHtml(d)}<span class="z"><i style="${d < 0 ? `right:50%` : `left:50%`};width:${w}px;background:${c}"></i></span></span>`;
}

async function abrirEstande(forcar) {
  if (ES && !forcar) return renderEstande();
  try {
    const r = await fetch('/api/estande/data?ts=' + Date.now()), j = await r.json();
    if (!r.ok) throw new Error(j.erro || 'Erro ao ler as planilhas de estande');
    ES = j; montarFiltros(); renderEstande();
  } catch (e) { toast(e.message, true) }
}
$('recarregar').addEventListener('click', () => { if (ES) abrirEstande(true) });

/* ---------- filtros ---------- */
let eDom = [-40, 40];
function montarFiltros() {
  const P = ES.parcelas, opc = (id, vals, todos) => {
    const el = $(id), v = el.value;
    el.innerHTML = `<option value="">${todos}</option>` + vals.map(x => `<option>${esc(x)}</option>`).join('');
    if (vals.includes(v)) el.value = v;
  };
  opc('eReg', [...new Set(P.map(r => r.micro))].sort(), 'Todas');
  opc('eTipo', [...new Set(P.map(r => r.tipo))].sort(), 'Todos');
  locOpts();
  $('eMats').innerHTML = [...new Set(P.map(r => r.nome))].sort().map(n => `<option value="${esc(n)}">`).join('');
  const ds = P.map(r => r.dif);
  eDom = ds.length ? [Math.floor(Math.min(...ds) / 5) * 5, Math.ceil(Math.max(...ds) / 5) * 5] : [-40, 40];
  ['eRMin', 'eRMax'].forEach(id => { $(id).min = eDom[0]; $(id).max = eDom[1]; $(id).step = 1 });
  syncFaixa();
}
function locOpts() {
  const reg = $('eReg').value, el = $('eLoc'), v = el.value;
  const ls = [...new Set(ES.parcelas.filter(r => !reg || r.micro === reg).map(r => r.local))].sort();
  el.innerHTML = '<option value="">Todas</option>' + ls.map(x => `<option>${esc(x)}</option>`).join('');
  if (ls.includes(v)) el.value = v;
}
const faixa = () => {
  const a = $('eMin').value, b = $('eMax').value;
  return [a === '' ? null : +a, b === '' ? null : +b];
};
function syncFaixa() {
  const [a, b] = faixa(), lo = a ?? eDom[0], hi = b ?? eDom[1];
  $('eRMin').value = lo; $('eRMax').value = hi;
  const W = eDom[1] - eDom[0] || 1;
  $('eSel').style.left = ((lo - eDom[0]) / W * 100) + '%';
  $('eSel').style.width = (Math.max(0, hi - lo) / W * 100) + '%';
}
$('eRMin').oninput = () => { let v = +$('eRMin').value; if (v > +$('eRMax').value) v = +$('eRMax').value; $('eMin').value = v <= eDom[0] ? '' : v; syncFaixa(); renderEstande() };
$('eRMax').oninput = () => { let v = +$('eRMax').value; if (v < +$('eRMin').value) v = +$('eRMin').value; $('eMax').value = v >= eDom[1] ? '' : v; syncFaixa(); renderEstande() };
['eMin', 'eMax'].forEach(id => $(id).oninput = () => { syncFaixa(); renderEstande() });
$('eRuim').onclick = () => { $('eMin').value = ''; $('eMax').value = RUIM; syncFaixa(); renderEstande() };
$('eLimpa').onclick = () => { ['eMin', 'eMax', 'eQ'].forEach(id => $(id).value = ''); ['eReg', 'eLoc', 'eTipo'].forEach(id => $(id).value = ''); locOpts(); syncFaixa(); renderEstande() };
$('eReg').onchange = () => { locOpts(); renderEstande() };
['eLoc', 'eTipo'].forEach(id => $(id).onchange = renderEstande);
$('eQ').oninput = renderEstande;
document.querySelectorAll('#eSubs button').forEach(b => b.onclick = () => {
  eSub = b.dataset.s;
  document.querySelectorAll('#eSubs button').forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('.esub').forEach(x => x.classList.toggle('on', x.id === 'es-' + eSub));
  renderEstande();
});
['aLim', 'aMin', 'rMin', 'rN', 'hOrd'].forEach(id => $(id).addEventListener('input', renderEstande));

function base() {
  const reg = $('eReg').value, loc = $('eLoc').value, tipo = $('eTipo').value, q = semAc($('eQ').value.trim());
  return ES.parcelas.filter(r => (!reg || r.micro === reg) && (!loc || r.local === loc) && (!tipo || r.tipo === tipo) && (!q || semAc(r.nome).includes(q)));
}
// faixa (a, b]: igual às barras do histograma, para os números baterem
const naFaixa = r => { const [a, b] = faixa(); return (a == null || r.dif > a || (a <= eDom[0] && r.dif >= a)) && (b == null || r.dif <= b) };
function textoFaixa() {
  const [a, b] = faixa();
  if (a == null && b == null) return 'todas as faixas';
  if (a == null) return `até ${pp(b)}`;
  if (b == null) return `a partir de ${pp(a)}`;
  return `de ${pp(a)} a ${pp(b)}`;
}

/* média da testemunha por localidade (independe dos filtros de tipo/material) */
function testemunhas() {
  const t = {};
  ES.parcelas.filter(r => r.tipo === 'Filtro').forEach(r => (t[r.local] = t[r.local] || []).push(r.dif));
  for (const k in t) t[k] = media(t[k]);
  return t;
}
/* agrega por material: média por localidade (repetições e Pop 1/3 viram uma média por local) */
function porMaterial(B) {
  const M = new Map(), T = testemunhas();
  B.forEach(r => {
    let m = M.get(r.k); if (!m) M.set(r.k, m = { k: r.k, nome: r.nome, tipo: r.tipo, L: {}, n: 0 });
    (m.L[r.local] = m.L[r.local] || { v: [], micro: r.micro }).v.push(r.dif);
    m.n++;
  });
  for (const m of M.values()) {
    m.locs = Object.entries(m.L).map(([local, o]) => ({ local, micro: o.micro, d: media(o.v) })).sort((a, b) => a.d - b.d);
    m.media = media(m.locs.map(x => x.d));
    const vs = m.locs.filter(x => T[x.local] != null && m.tipo !== 'Filtro').map(x => x.d - T[x.local]);
    m.vsT = vs.length ? media(vs) : null;
  }
  return [...M.values()];
}

/* ---------- render ---------- */
function renderEstande() {
  if (!ES) return;
  const B = base();
  ({ geral: rGeral, ajuste: rAjuste, rank: rRank, mapa: rMapa, parc: rParc, arq: rArq })[eSub](B);
}

function rGeral(B) {
  const F = B.filter(naFaixa), n = B.length;
  const c = { r: 0, a: 0, o: 0 }; B.forEach(r => c[st(r.dif)]++);
  const pc = x => n ? Math.round(x / n * 100) : 0;
  const ds = B.map(r => r.dif).sort((a, b) => a - b), med = ds.length ? ds[Math.floor(ds.length / 2)] : null;
  $('eK').innerHTML = `
    <div class="kpi"><div class="l">Parcelas avaliadas</div><div class="v">${n}</div><div class="d">${new Set(B.map(r => r.local)).size} localidades · ${new Set(B.map(r => r.k)).size} materiais</div></div>
    <div class="kpi hl"><div class="l">Na faixa selecionada</div><div class="v">${F.length} <small>${pc(F.length)}%</small></div><div class="d">diferença ${textoFaixa()}</div></div>
    <div class="kpi"><div class="l">Estande ruim (−15% ou pior)</div><div class="v" style="color:var(--bad)">${c.r} <small>${pc(c.r)}%</small></div><div class="d">${c.a} em atenção (entre −15% e −10%)</div></div>
    <div class="kpi"><div class="l">Diferença média</div><div class="v">${n ? pp(media(ds)) : '–'}</div><div class="d">mediana ${med == null ? '–' : pp(med)}</div></div>`;
  $('eStat').innerHTML = n ? ['o', 'a', 'r'].map(s => c[s] ? `<div style="flex:${c[s]};background:${COR[s]}" title="${STN[s]}: ${c[s]}">${pc(c[s]) >= 6 ? pc(c[s]) + '%' : ''}</div>` : '').join('') : '';
  $('eStatL').innerHTML = ['o', 'a', 'r'].map(s => `<span><b style="background:${COR[s]}"></b>${STN[s]}: <strong>${c[s]}</strong> parcelas (${pc(c[s])}%)</span>`).join('');
  histograma(B);
  // localidades
  const T = testemunhas(), L = {};
  B.forEach(r => (L[r.local] = L[r.local] || { micro: r.micro, v: [], piores: [] }).v.push(r));
  const linhas = Object.entries(L).map(([loc, o]) => {
    const d = o.v.map(r => r.dif), pior = o.v.reduce((a, b) => a.dif < b.dif ? a : b);
    return { loc, micro: o.micro, n: d.length, m: media(d), t: T[loc], ruim: d.filter(x => x <= RUIM).length, pior };
  }).sort((a, b) => a.m - b.m);
  $('eLocT').innerHTML = `<thead><tr><th style="text-align:left">Localidade</th><th>Região</th><th>Parcelas</th><th>Dif. média</th><th>Ruins</th><th style="text-align:left">Pior material</th></tr></thead><tbody>` +
    linhas.map(x => `<tr class="clk" data-loc="${esc(x.loc)}"><td class="t"><b>${esc(x.loc)}</b></td><td>${x.micro}</td><td>${x.n}</td><td>${difHtml(x.m)}</td><td>${x.ruim ? `<span class="chip bad">${x.ruim}</span>` : '0'}</td><td class="t">${esc(x.pior.nome)} ${difHtml(x.pior.dif)}</td></tr>`).join('') + '</tbody>';
  $('eLocT').querySelectorAll('tr.clk').forEach(tr => tr.onclick = () => { $('eLoc').value = tr.dataset.loc; renderEstande() });
  materiaisFaixa(B);
}

function histograma(B) {
  const box = $('eHist'); if (!box.offsetWidth) return;
  const [fa, fb] = faixa(), lo = eDom[0], hi = eDom[1], bins = [];
  for (let a = lo; a < hi; a += 5) bins.push({ a, b: a + 5, n: B.filter(r => (r.dif > a || (a === lo && r.dif >= lo)) && r.dif <= a + 5).length });
  const W = box.offsetWidth, H = 230, m = { l: 36, r: 10, t: 14, b: 28 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
  const mx = Math.max(1, ...bins.map(b => b.n)), bw = iw / bins.length;
  const X = v => m.l + (v - lo) / (hi - lo) * iw, Y = n => m.t + ih - n / mx * ih;
  let g = '';
  const passo = mx > 50 ? 20 : mx > 20 ? 10 : 5;
  for (let v = 0; v <= mx; v += passo) g += `<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e6eef1"/><text x="${m.l - 6}" y="${Y(v) + 4}" text-anchor="end" font-size="11" fill="#6b7f8a">${v}</text>`;
  bins.forEach((b, i) => {
    const s = b.b <= RUIM ? 'r' : b.b <= ATENC ? 'a' : 'o', dentro = (fa == null || b.b > fa) && (fb == null || b.a < fb);
    const x = X(b.a) + 1, w = Math.max(1, bw - 2), y = Y(b.n);
    if (b.n) g += `<path d="M${x},${m.t + ih}V${y + 3}q0,-3 3,-3h${w - 6}q3,0 3,3V${m.t + ih}Z" fill="${b.a >= 0 ? COR.p : COR[s]}" opacity="${dentro ? 1 : .22}"/>`;
    if (b.n && bw > 22) g += `<text x="${x + w / 2}" y="${y - 4}" text-anchor="middle" font-size="10" fill="#40596a">${b.n}</text>`;
    g += `<rect class="hb" data-i="${i}" x="${X(b.a)}" y="${m.t}" width="${bw}" height="${ih}" fill="transparent"/>`;
  });
  for (let v = lo; v <= hi; v += 10) g += `<text x="${X(v)}" y="${H - 8}" text-anchor="middle" font-size="11" fill="#6b7f8a">${v > 0 ? '+' : ''}${v}%</text>`;
  if (RUIM > lo) g += `<line x1="${X(RUIM)}" x2="${X(RUIM)}" y1="${m.t - 4}" y2="${m.t + ih}" stroke="#c62828" stroke-dasharray="4 3"/><text x="${X(RUIM) - 4}" y="${m.t + 6}" text-anchor="end" font-size="11" font-weight="700" fill="#c62828">benchmark −15%</text>`;
  if (0 > lo && 0 < hi) g += `<line x1="${X(0)}" x2="${X(0)}" y1="${m.t}" y2="${m.t + ih}" stroke="#08243d" opacity=".35"/>`;
  box.querySelector('svg')?.remove();
  box.insertAdjacentHTML('afterbegin', `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Histograma da diferença de população">${g}</svg>`);
  const tip = $('eHistTip');
  box.querySelectorAll('.hb').forEach(r => {
    r.onmousemove = e => {
      const i = +r.dataset.i, b = bins[i], bb = box.getBoundingClientRect();
      if (eArr != null) { const i0 = Math.min(eArr, i), i1 = Math.max(eArr, i); eArrFim = i; box.querySelectorAll('.hb').forEach(x => x.setAttribute('fill', +x.dataset.i >= i0 && +x.dataset.i <= i1 ? 'rgba(0,103,122,.12)' : 'transparent')) }
      tip.innerHTML = `<b>${pp(b.a)} a ${pp(b.b)}</b>${b.n} parcela${b.n === 1 ? '' : 's'} (${B.length ? Math.round(b.n / B.length * 100) : 0}%)<div class="note">clique ou arraste para ver os materiais</div>`; tip.style.display = 'block'; tip.style.left = Math.min(e.clientX - bb.left + 12, bb.width - 190) + 'px'; tip.style.top = '8px';
    };
    r.onmouseleave = () => tip.style.display = 'none';
    r.onmousedown = e => { e.preventDefault(); eArr = eArrFim = +r.dataset.i };
  });
  box.onmouseup = () => {
    if (eArr == null) return;
    const i0 = Math.min(eArr, eArrFim), i1 = Math.max(eArr, eArrFim), a = bins[i0].a, b = bins[i1].b; eArr = null;
    const [fa, fb] = faixa();
    if (i0 === i1 && fa === a && fb === b) { $('eMin').value = ''; $('eMax').value = '' } else { $('eMin').value = a; $('eMax').value = b }
    syncFaixa(); renderEstande();
  };
}

let aLinhas = [];
function rAjuste(B) {
  const lim = +$('aLim').value, mn = Math.max(1, +$('aMin').value || 1), M = porMaterial(B);
  const regs = [...new Set(B.map(r => r.micro))].sort();
  const aj = d => d < 0 ? (1 / (1 + d / 100) - 1) * 100 : 0;
  aLinhas = M.map(m => ({ m, ruins: m.locs.filter(x => x.d <= lim) })).filter(x => x.ruins.length >= mn)
    .sort((a, b) => b.ruins.length - a.ruins.length || a.m.media - b.m.media);
  $('aInfo').textContent = `${aLinhas.length} cultivares com estande ${pp(lim)} ou pior em ${mn} ou mais localidades`;
  $('aT').innerHTML = `<thead><tr><th style="text-align:left">Cultivar</th><th>Tipo</th><th>Locais abaixo<br>do limite</th><th>Dif. média</th><th>Ajuste sugerido<br>(todas as regiões)</th>${regs.map(g => `<th>${g}<br><small>dif. → ajuste</small></th>`).join('')}<th style="text-align:left">Por localidade</th></tr></thead><tbody>` +
    (aLinhas.length ? aLinhas.map(({ m, ruins }) => {
      const porReg = regs.map(g => { const v = m.locs.filter(x => x.micro === g); if (!v.length) return '<td class="note">–</td>'; const d = media(v.map(x => x.d)); return `<td>${difHtml(d)}${d <= lim ? ` → <b>+${aj(d).toFixed(0)}%</b>` : ' <span class="note">ok</span>'}</td>` }).join('');
      return `<tr><td class="t"><b>${esc(m.nome)}</b></td><td>${esc(m.tipo)}</td><td><b>${ruins.length}</b> de ${m.locs.length}</td><td>${difHtml(m.media)}</td><td>${m.media < 0 ? `<span class="chip warn" style="font-size:13px">+${aj(m.media).toFixed(0)}% sementes</span>` : '–'}</td>${porReg}<td class="t"><div class="locs">${m.locs.map(x => `<span class="${x.d <= lim ? st(x.d) === 'r' ? 'r' : 'a' : ''}">${esc(x.local)} ${pp(x.d)}</span>`).join('')}</div></td></tr>`;
    }).join('') : `<tr><td colspan="${6 + regs.length}" class="empty" style="text-align:center;padding:24px">Nenhuma cultivar com ${pp(lim)} ou pior em ${mn} ou mais localidades com os filtros atuais.</td></tr>`) + '</tbody>';
}
$('aCsv').onclick = () => {
  const lim = +$('aLim').value, regs = [...new Set(base().map(r => r.micro))].sort(), aj = d => d < 0 ? (1 / (1 + d / 100) - 1) * 100 : 0;
  csv('ajuste_semeadura.csv', [['Cultivar', 'Tipo', 'Locais abaixo do limite', 'Locais avaliados', 'Dif. média (%)', 'Ajuste sugerido (% sementes)', ...regs.flatMap(g => [g + ' dif. (%)', g + ' ajuste (%)']), 'Localidades']].concat(
    aLinhas.map(({ m, ruins }) => [m.nome, m.tipo, ruins.length, m.locs.length, m.media.toFixed(1), aj(m.media).toFixed(0), ...regs.flatMap(g => { const v = m.locs.filter(x => x.micro === g); if (!v.length) return ['', '']; const d = media(v.map(x => x.d)); return [d.toFixed(1), d <= lim ? aj(d).toFixed(0) : ''] }), m.locs.map(x => `${x.local} ${x.d.toFixed(1)}%`).join(' | ')])));
};

function rRank(B) {
  const mn = Math.max(1, +$('rMin').value || 1), N = +$('rN').value, M = porMaterial(B).filter(m => m.locs.length >= mn);
  const tab = (lista, alvo) => {
    $(alvo).innerHTML = `<thead><tr><th>#</th><th style="text-align:left">Cultivar</th><th>Locais</th><th>Dif. média</th><th>vs. Filtro</th><th>Ruins</th></tr></thead><tbody>` +
      (lista.length ? lista.slice(0, N).map((m, i) => `<tr><td class="note">${i + 1}</td><td class="t"><b>${esc(m.nome)}</b><div class="note">${esc(m.tipo)}</div></td><td>${m.locs.length}</td><td>${dvBar(m.media)}</td><td>${m.vsT == null ? '<span class="note">–</span>' : `<span class="dif ${m.vsT < -5 ? 'r' : 'o'}">${(m.vsT > 0 ? '+' : '') + m.vsT.toFixed(1).replace('.', ',')} p.p.</span>`}</td><td>${(c => c ? `<span class="chip bad">${c}/${m.locs.length}</span>` : '0')(m.locs.filter(x => x.d <= RUIM).length)}</td></tr>`).join('')
        : `<tr><td colspan="6" class="empty" style="text-align:center;padding:20px">Nenhuma cultivar avaliada em ${mn} ou mais localidades.</td></tr>`) + '</tbody>';
  };
  tab([...M].sort((a, b) => a.media - b.media), 'rPior');
  tab([...M].sort((a, b) => Math.abs(a.media) - Math.abs(b.media)), 'rMelhor');
}

function corHeat(d) {
  const t = Math.max(-1, Math.min(1, d / 30)), a = Math.abs(t), base = [244, 246, 247], fim = t < 0 ? [183, 28, 28] : [0, 61, 166];
  const c = base.map((v, i) => Math.round(v + (fim[i] - v) * Math.pow(a, .8)));
  return `background:rgb(${c});color:${a > .55 ? '#fff' : '#08243d'}`;
}
function rMapa(B) {
  const M = porMaterial(B), locs = [...new Set(B.map(r => r.micro + '|' + r.local))].sort().map(x => x.split('|')[1]);
  const o = $('hOrd').value;
  M.sort(o === 'n' ? (a, b) => a.nome.localeCompare(b.nome) : o === 't' ? (a, b) => a.tipo.localeCompare(b.tipo) || a.media - b.media : (a, b) => a.media - b.media);
  const micro = {}; B.forEach(r => micro[r.local] = r.micro);
  $('hT').innerHTML = `<thead><tr><th style="text-align:left;left:0;z-index:3">Cultivar (${M.length})</th>${locs.map(l => `<th class="v" title="${esc(l)}">${esc(l)} <span class="note">${micro[l]}</span></th>`).join('')}<th class="v">Média</th></tr></thead><tbody>` +
    M.map(m => `<tr><td class="n">${esc(m.nome)}</td>${locs.map(l => { const x = m.locs.find(y => y.local === l); return x ? `<td style="${corHeat(x.d)}" title="${esc(m.nome)} · ${esc(l)}: ${pp(x.d)}">${x.d.toFixed(0)}</td>` : '<td class="na">·</td>' }).join('')}<td style="${corHeat(m.media)};font-weight:800">${m.media.toFixed(1).replace('.', ',')}</td></tr>`).join('') + '</tbody>';
}

let pOrd = { c: 'dif', asc: true };
const PCOLS = [['local', 'Localidade'], ['micro', 'Região'], ['nome', 'Cultivar'], ['tipo', 'Tipo'], ['alvo', 'Pop. recomendada'], ['estande', 'Estande inicial'], ['dif', 'Dif. população'], ['st', 'Status']];
function tabParcelas(lista, el, ord, refazer) {
  const F = lista.map(r => ({ ...r, st: STN[st(r.dif)] }));
  const { c, asc } = ord;
  F.sort((a, b) => { const x = a[c], y = b[c]; const v = typeof x === 'number' && typeof y === 'number' ? x - y : String(x ?? '').localeCompare(String(y ?? ''), 'pt', { numeric: true }); return asc ? v : -v });
  el.innerHTML = `<thead><tr>${PCOLS.map(([k, t]) => `<th class="s" data-c="${k}">${t}${k === c ? (asc ? ' ▲' : ' ▼') : ''}</th>`).join('')}</tr></thead><tbody>` +
    F.map(r => `<tr><td class="t">${esc(r.local)}</td><td>${r.micro}</td><td class="t"><b>${esc(r.nome)}</b>${r.pop ? ` <span class="note">${r.pop}</span>` : ''}</td><td>${esc(r.tipo)}</td><td>${pt(r.alvo)}</td><td>${pt(r.estande)}</td><td>${difHtml(r.dif)}</td><td><span class="chip ${({ r: 'bad', a: 'warn', o: 'ok' })[st(r.dif)]}">${r.st}</span></td></tr>`).join('') + '</tbody>';
  el.querySelectorAll('th.s').forEach(th => th.onclick = () => { ord.asc = ord.c === th.dataset.c ? !ord.asc : true; ord.c = th.dataset.c; refazer() });
  if (!F.length) el.innerHTML += `<tbody><tr><td colspan="${PCOLS.length}" class="empty" style="text-align:center;padding:20px">Nenhuma parcela nesta faixa.</td></tr></tbody>`;
}
function rParc(B) {
  const F = B.filter(naFaixa);
  $('pInfo').innerHTML = `<b>${F.length}</b> de ${B.length} parcelas (${B.length ? Math.round(F.length / B.length * 100) : 0}%) com diferença ${textoFaixa()}. Clique no título da coluna para ordenar.`;
  tabParcelas(F, $('pT'), pOrd, () => rParc(base()));
}
/* materiais da faixa escolhida no histograma (visão geral) */
let mModo = 'p', mOrd = { c: 'dif', asc: true };
document.querySelectorAll('#mModo button').forEach(b => b.onclick = () => { mModo = b.dataset.m; document.querySelectorAll('#mModo button').forEach(x => x.classList.toggle('on', x === b)); materiaisFaixa(base()) });
function materiaisFaixa(B) {
  const F = B.filter(naFaixa), [a, b] = faixa(), nMat = new Set(F.map(r => r.k)).size;
  $('mTit').textContent = a == null && b == null ? 'Materiais — todas as faixas' : `Materiais com diferença ${textoFaixa()}`;
  $('mSub').innerHTML = `<b>${F.length}</b> parcela${F.length === 1 ? '' : 's'} (${B.length ? Math.round(F.length / B.length * 100) : 0}%) · <b>${nMat}</b> materia${nMat === 1 ? 'l' : 'is'}` + (a == null && b == null ? ' · selecione uma faixa no gráfico acima' : ` · <a href="#" id="mLimpa" style="color:var(--teal2);font-weight:700">limpar seleção</a>`);
  const lk = $('mLimpa'); if (lk) lk.onclick = e => { e.preventDefault(); $('eMin').value = ''; $('eMax').value = ''; syncFaixa(); renderEstande() };
  if (mModo === 'p') return tabParcelas(F, $('mT'), mOrd, () => materiaisFaixa(base()));
  const G = new Map();
  F.forEach(r => { let g = G.get(r.k); if (!g) G.set(r.k, g = { nome: r.nome, tipo: r.tipo, v: [] }); g.v.push(r) });
  const linhas = [...G.values()].map(g => ({ ...g, m: media(g.v.map(r => r.dif)) })).sort((x, y) => y.v.length - x.v.length || x.m - y.m);
  $('mT').innerHTML = `<thead><tr><th style="text-align:left">Cultivar</th><th>Tipo</th><th>Parcelas na faixa</th><th>Dif. média na faixa</th><th style="text-align:left">Localidades</th></tr></thead><tbody>` +
    (linhas.length ? linhas.map(g => `<tr><td class="t"><b>${esc(g.nome)}</b></td><td>${esc(g.tipo)}</td><td><b>${g.v.length}</b></td><td>${difHtml(g.m)}</td><td class="t"><div class="locs">${g.v.sort((x, y) => x.dif - y.dif).map(r => `<span class="${st(r.dif) === 'o' ? '' : st(r.dif)}">${esc(r.local)} ${pp(r.dif)}</span>`).join('')}</div></td></tr>`).join('')
      : `<tr><td colspan="5" class="empty" style="text-align:center;padding:20px">Nenhuma parcela nesta faixa.</td></tr>`) + '</tbody>';
}
$('pCsv').onclick = () => {
  const F = base().filter(naFaixa);
  csv('parcelas_estande.csv', [['Localidade', 'Região', 'Cultivar', 'Variação', 'Tipo', 'Pop. recomendada', 'Estande inicial', 'Dif. população (%)', 'Status', 'Arquivo']].concat(
    F.map(r => [r.local, r.micro, r.nome, r.pop ?? '', r.tipo, r.alvo == null ? '' : Math.round(r.alvo), r.estande == null ? '' : Math.round(r.estande), r.dif.toFixed(1), STN[st(r.dif)], r.arquivo])));
};

function rArq() {
  $('fT').innerHTML = `<thead><tr><th style="text-align:left">Arquivo</th><th>Situação</th><th>Modelo</th><th>Localidade</th><th>Região</th><th>Parcelas</th><th>Materiais</th><th></th></tr></thead><tbody>` +
    ES.arquivos.map(a => `<tr><td class="t"><b>${esc(a.arquivo)}</b></td><td>${!a.ok ? `<span class="chip bad" title="${esc(a.erro)}">Erro</span><div class="note">${esc(a.erro)}</div>` : a.ignorado ? `<span class="chip warn">Ignorado</span><div class="note">${esc(a.ignorado)}</div>` : '<span class="chip ok">Lido</span>'}</td><td>${esc(a.formato || '')}</td><td>${esc(a.local || '')}</td><td>${a.micro || ''}</td><td>${a.parcelas ?? ''}</td><td>${a.materiais ?? ''}</td><td style="white-space:nowrap"><button class="btn" data-xl="${esc(a.arquivo)}">Abrir no Excel</button> <button class="btn dng ${eConf === a.arquivo ? 'sure' : ''}" data-rm="${esc(a.arquivo)}">${eConf === a.arquivo ? 'Confirmar' : 'Remover'}</button></td></tr>`).join('') + '</tbody>';
  $('fT').querySelectorAll('[data-xl]').forEach(b => b.onclick = async () => {
    try { const r = await fetch('/api/estande/abrir', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ arquivo: b.dataset.xl }) }), j = await r.json(); if (!r.ok) throw new Error(j.erro); toast('Abrindo no Excel. Depois de salvar e fechar, clique em ↻ Atualizar dados.') } catch (e) { toast(e.message, true) }
  });
  $('fT').querySelectorAll('[data-rm]').forEach(b => b.onclick = async () => {
    const f = b.dataset.rm;
    if (eConf !== f) { eConf = f; rArq(); setTimeout(() => { if (eConf === f) { eConf = null; rArq() } }, 5000); return }
    eConf = null;
    try { const r = await fetch('/api/estande/remover', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ arquivo: f }) }), j = await r.json(); if (!r.ok) throw new Error(j.erro); ES = j; montarFiltros(); renderEstande(); toast(f + ' removido (cópia guardada em dados/uploads_removidos).') } catch (e) { toast(e.message, true) }
  });
  $('uL').innerHTML = ES.unificados.length ? `<div class="locs">${ES.unificados.map(u => `<span title="${esc(u.variantes.join(' · '))}"><b>${esc(u.nome)}</b> ← ${u.variantes.map(esc).join(' · ')}</span>`).join('')}</div>` : '<div class="empty">Nenhuma grafia diferente encontrada.</div>';
}
async function enviar(files) {
  const fd = new FormData(); let n = 0;
  [...files].forEach(f => { if (f.name.toLowerCase().endsWith('.xlsx')) { fd.append('files', f, f.name); n++ } });
  if (!n) return toast('Envie arquivos .xlsx', true);
  try {
    const r = await fetch('/api/estande/upload', { method: 'POST', body: fd }), j = await r.json();
    if (!r.ok) throw new Error(j.erro || 'Erro no envio');
    ES = j.result; montarFiltros(); renderEstande();
    const ok = ES.arquivos.filter(a => j.saved.includes(a.arquivo));
    const erros = ok.filter(a => !a.ok);
    toast(erros.length ? `${erros.length} arquivo(s) não reconhecido(s): veja a lista.` : `${ok.length} planilha(s) incluída(s): ${ok.map(a => a.local).join(', ')}.`, !!erros.length);
  } catch (e) { toast(e.message, true) }
}
$('eDrop').onclick = () => $('eFile').click();
$('eFile').onchange = e => { enviar(e.target.files); e.target.value = '' };
['dragenter', 'dragover'].forEach(ev => $('eDrop').addEventListener(ev, e => { e.preventDefault(); $('eDrop').classList.add('over') }));
['dragleave', 'drop'].forEach(ev => $('eDrop').addEventListener(ev, e => { e.preventDefault(); $('eDrop').classList.remove('over') }));
$('eDrop').addEventListener('drop', e => enviar(e.dataTransfer.files));

function csv(nome, linhas) {
  const txt = '﻿' + linhas.map(l => l.map(v => { const s = String(v ?? '').replace(/^(-?\d+)\.(\d+)$/, '$1,$2'); return /[;"\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s }).join(';')).join('\r\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], { type: 'text/csv;charset=utf-8' })); a.download = nome; document.body.appendChild(a); a.click(); a.remove();
}
let eRz; window.addEventListener('resize', () => { clearTimeout(eRz); eRz = setTimeout(() => { if (ES && eSub === 'geral') renderEstande() }, 150) });
