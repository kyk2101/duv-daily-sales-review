"""DUVETICA 매출 리뷰 모바일 HTML 빌더 - 시즌 우선 구조."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "src" / "output"
DATA_DIR = PROJECT_ROOT / "data"

DATA_FILE = DATA_DIR / "duv_review_data.json"
# index.html을 리포 루트에 두면 GitHub Pages가 자동으로 entry로 인식
HTML_ROOT = PROJECT_ROOT / "index.html"
HTML_OUTPUT = OUTPUT_DIR / "duvetica_sales_review.html"


HTML_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="theme-color" content="#0e0e10" />
<title>DUVETICA 매출 리뷰</title>
<style>
  :root {
    --bg: #0e0e10;
    --bg-elev: #18181b;
    --bg-card: #1f1f23;
    --line: #2a2a30;
    --text: #f4f4f5;
    --text-2: #a1a1aa;
    --text-3: #71717a;
    --accent: #c8a96a;
    --accent-soft: rgba(200,169,106,0.15);
    --up: #22c55e;
    --down: #ef4444;
    --neutral: #6b8cce;
    --shadow: 0 8px 24px rgba(0,0,0,0.35);
    --radius: 14px;
    --gap: 12px;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html, body { margin:0; padding:0; background:var(--bg); color:var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro KR", "Apple SD Gothic Neo",
                 "Pretendard", "Noto Sans KR", "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased; }
  body { min-height: 100vh; min-height: 100dvh; }
  .wrap { max-width: 520px; margin: 0 auto; padding: 0 16px 80px;
          padding-top: calc(env(safe-area-inset-top, 0px) + 14px); }

  /* HEADER */
  header.app-hd { display:flex; align-items:center; justify-content:space-between;
    padding: 8px 0 14px; }
  .brand {
    font-weight: 700; letter-spacing: 0.18em; font-size: 18px;
    background: linear-gradient(135deg, #fff 0%, var(--accent) 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .as-of { font-size: 11px; color: var(--text-3); text-align: right; line-height: 1.4; }

  /* SEASON HERO TAB — 최상단 대전제 */
  .season-hero {
    background: linear-gradient(135deg, #1c1c20 0%, #15151a 100%);
    border:1px solid var(--line);
    border-radius: 16px;
    padding: 4px;
    margin-bottom: 18px;
    display:flex;
    box-shadow: var(--shadow);
    position: sticky; top: 6px; z-index: 30;
  }
  .season-hero .hero-tab {
    flex:1; text-align:center; padding:14px 0;
    border-radius: 13px;
    font-size: 16px; font-weight: 700; letter-spacing: 0.06em;
    color: var(--text-3); cursor:pointer; user-select:none;
    transition: all 0.18s ease;
    position: relative;
  }
  .season-hero .hero-tab .label { font-size: 16px; }
  .season-hero .hero-tab .sub { font-size: 10.5px; color: var(--text-3); display:block; margin-top:4px; font-weight:500; letter-spacing: 0; }
  .season-hero .hero-tab.active {
    background: linear-gradient(135deg, var(--accent) 0%, #b08c4a 100%);
    color: #1a1a1a;
    box-shadow: 0 4px 14px rgba(200,169,106,0.35);
  }
  .season-hero .hero-tab.active .sub { color: rgba(26,26,26,0.7); }

  /* INSIGHTS — horizontal scroll cards */
  .insight-row { display:flex; gap:10px; overflow-x:auto; padding-bottom:8px;
    scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; }
  .insight-row::-webkit-scrollbar { display:none; }
  .insight {
    min-width: 240px; flex:0 0 auto; background:var(--bg-card);
    border:1px solid var(--line); border-radius:var(--radius);
    padding:14px 14px 12px; scroll-snap-align: start;
  }
  .insight .t { font-size:11px; color:var(--text-3); letter-spacing:0.04em; }
  .insight .v { font-size:22px; font-weight:700; margin-top:8px; line-height:1.2;
    word-break: keep-all; }
  .insight .d { display:flex; align-items:center; gap:6px; margin-top:6px;
    font-size: 12px; flex-wrap: wrap; }
  .insight .d .delta { font-weight:600; }
  .insight .d.up .delta { color: var(--up); }
  .insight .d.down .delta { color: var(--down); }
  .insight .d.neutral .delta { color: var(--neutral); }
  .insight .d .desc { color: var(--text-3); }

  /* SECTION HEADERS */
  h2.sect { margin: 24px 0 10px; font-size:15px; font-weight:600;
    letter-spacing:0.04em; display:flex; align-items:center; gap:8px; }
  h2.sect::before { content:""; width:3px; height:14px; background:var(--accent);
    border-radius:2px; }

  /* SUB-TABS — sort metric */
  .stabs { display:flex; gap:6px; margin-bottom:12px; }
  .stab { padding:7px 12px; border-radius:999px; border:1px solid var(--line);
    background:transparent; color:var(--text-2); font-size:12px; cursor:pointer;
    user-select:none; }
  .stab.active { background:var(--accent); color:#1a1a1a; border-color:var(--accent);
    font-weight:600; }

  .season-summary { display:flex; gap:8px; padding:10px 12px; background:var(--bg-elev);
    border:1px solid var(--line); border-radius:10px; margin-bottom:10px;
    font-size:12px; color: var(--text-2); justify-content:space-between; flex-wrap:wrap; }
  .season-summary b { color: var(--text); font-weight:600; }

  /* CARD GRID */
  .grid { display:grid; grid-template-columns: 1fr; gap: var(--gap); }
  @media(min-width: 420px){ .grid { grid-template-columns: 1fr 1fr; } }

  .card { background:var(--bg-card); border:1px solid var(--line);
    border-radius:var(--radius); overflow:hidden; position:relative;
    display:flex; flex-direction:column; }
  .card .imgwrap { aspect-ratio: 1 / 1; background:#0a0a0c;
    display:flex; align-items:center; justify-content:center; overflow:hidden;
    position:relative; }
  .card img { width:100%; height:100%; object-fit:cover; display:block; }
  .card .placeholder { color:var(--text-3); font-size:11px; }
  .card .rank { position:absolute; left:8px; top:8px;
    background: rgba(14,14,16,0.85); color:var(--accent);
    font-size:11px; font-weight:700; letter-spacing:0.05em;
    padding:4px 8px; border-radius:6px; border:1px solid rgba(200,169,106,0.35); }
  .card .crown { position:absolute; right:8px; top:8px; font-size:18px; opacity:0.95; }
  .card .body { padding:10px 12px 12px; }
  .card .nm { font-size:13px; font-weight:600; line-height:1.35;
    overflow:hidden; text-overflow:ellipsis; display:-webkit-box;
    -webkit-line-clamp:2; -webkit-box-orient:vertical; min-height:2.7em; }
  .card .meta { font-size:10.5px; color:var(--text-3); margin-top:4px;
    display:flex; gap:6px; flex-wrap:wrap; }
  .card .meta .badge { background:rgba(255,255,255,0.05);
    padding:2px 6px; border-radius:4px; }
  .card .stats { margin-top:8px; padding-top:8px; border-top:1px solid var(--line);
    display:flex; justify-content:space-between; align-items:flex-end; }
  .card .stats .amt { font-size:14px; font-weight:700; color:var(--text); }
  .card .stats .qty { font-size:11px; color:var(--text-2); }
  .card .salert { font-size:10.5px; color:var(--text-3); margin-top:4px; }
  .card .salert .bar { display:inline-block; height:3px; width:60px;
    background:rgba(255,255,255,0.08); border-radius:2px; vertical-align:middle;
    overflow:hidden; margin-left:6px; }
  .card .salert .bar i { display:block; height:100%; background:var(--accent);
    border-radius:2px; }

  /* COLOR BREAKDOWN — inside card */
  .colors {
    margin-top: 8px; padding-top: 8px;
    border-top: 1px dashed var(--line);
  }
  .colors .colors-hd { font-size: 10px; color: var(--text-3);
    letter-spacing: 0.05em; margin-bottom: 6px; }
  .colors .clist { display:flex; flex-direction:column; gap:4px; }
  .colors .crow { display:flex; align-items:center; gap:8px;
    font-size: 11px; }
  .colors .crow .ccd { font-weight: 600; min-width: 36px;
    background: var(--bg-elev); border:1px solid var(--line);
    padding: 1px 6px; border-radius: 4px; text-align:center;
    font-size: 10.5px; letter-spacing: 0.04em; }
  .colors .crow .cbar { flex: 1; height: 6px; background: rgba(255,255,255,0.04);
    border-radius: 3px; overflow: hidden; }
  .colors .crow .cbar i { display:block; height:100%; border-radius: 3px;
    background: linear-gradient(90deg, var(--accent) 0%, #d8c08e 100%); }
  .colors .crow .cqty { color: var(--text-2); min-width: 50px; text-align: right;
    font-variant-numeric: tabular-nums; }
  .colors .crow .cqty b { color: var(--text); font-weight: 600; }

  /* SHOPS */
  .shop {
    background:var(--bg-card); border:1px solid var(--line);
    border-radius: var(--radius); margin-bottom:10px; overflow:hidden;
  }
  .shop summary {
    list-style: none; cursor:pointer; padding:14px 14px;
    display:flex; align-items:center; gap:10px;
  }
  .shop summary::-webkit-details-marker { display:none; }
  .shop summary .rank-circle {
    width:30px; height:30px; border-radius:50%; flex-shrink:0;
    background:var(--bg-elev); border:1px solid var(--line);
    color:var(--accent); font-size:12px; font-weight:700;
    display:flex; align-items:center; justify-content:center;
  }
  .shop summary .info { flex:1; min-width:0; }
  .shop summary .info .nm { font-size:14px; font-weight:600;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .shop summary .info .sub { font-size:11px; color:var(--text-3); margin-top:2px; }
  .shop summary .right { text-align:right; flex-shrink:0; }
  .shop summary .right .a { font-size:13px; font-weight:700; }
  .shop summary .right .q { font-size:11px; color:var(--text-3); margin-top:2px; }
  .shop summary .chev { color: var(--text-3); transition: transform 0.2s; margin-left:6px; }
  .shop[open] summary .chev { transform: rotate(180deg); }
  .shop .styles { padding: 0 14px 14px 14px; border-top:1px solid var(--line); }
  .shop .style-row { display:flex; gap:10px; padding:10px 0;
    border-bottom:1px dashed var(--line); align-items:center; }
  .shop .style-row:last-child { border-bottom:none; }
  .shop .style-row .sr { font-size:11px; font-weight:700; color:var(--text-3);
    width:18px; flex-shrink:0; }
  .shop .style-row .sn { flex:1; min-width:0; font-size:12.5px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .shop .style-row .si { font-size:10.5px; color:var(--text-3); }
  .shop .style-row .sa { font-size:12.5px; font-weight:600; text-align:right;
    flex-shrink:0; min-width:80px; }
  .shop .style-row .sq { font-size:10.5px; color:var(--text-3); margin-top:2px; }

  /* DAILY TREND */
  .trend { background:var(--bg-card); border:1px solid var(--line);
    border-radius:var(--radius); padding: 14px; margin-bottom: 10px; }
  .trend-bars { display:flex; align-items:flex-end; gap:10px;
    height:120px; padding:6px 0 0; }
  .trend-bar { flex:1; display:flex; flex-direction:column;
    align-items:center; gap:6px; }
  .trend-bar .b {
    width:100%; min-height:4px; border-radius:6px 6px 0 0;
    background: linear-gradient(180deg, var(--accent) 0%, #8a7345 100%);
    transition: opacity 0.2s;
  }
  .trend-bar.today .b {
    background: linear-gradient(180deg, #f4d896 0%, var(--accent) 100%);
    box-shadow: 0 0 12px rgba(200,169,106,0.4);
  }
  .trend-bar.empty .b { background: rgba(255,255,255,0.05); }
  .trend-bar .lbl { font-size:10px; color:var(--text-3); }
  .trend-bar .v { font-size:10.5px; color:var(--text); font-weight:600; }

  /* YESTERDAY TOP */
  .yt { background:var(--bg-card); border:1px solid var(--line);
    border-radius:var(--radius); overflow:hidden; }
  .yt .row { display:flex; gap:10px; padding:10px 14px; align-items:center;
    border-bottom:1px solid var(--line); }
  .yt .row:last-child { border-bottom:none; }
  .yt .rk { font-size:12px; font-weight:700; color:var(--accent); width:22px;
    flex-shrink:0; }
  .yt .ct { flex:1; min-width:0; }
  .yt .ct .n { font-size:13px; font-weight:600;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .yt .ct .m { font-size:11px; color:var(--text-3); margin-top:2px; }
  .yt .vv { text-align:right; flex-shrink:0; }
  .yt .vv .a { font-size:13px; font-weight:700; }
  .yt .vv .q { font-size:11px; color:var(--text-3); }
  .empty-state { text-align:center; padding:24px 12px; color:var(--text-3);
    font-size:12.5px; background:var(--bg-card); border:1px dashed var(--line);
    border-radius: var(--radius); }

  /* FOOTER */
  footer { text-align:center; color:var(--text-3); font-size:10.5px;
    margin-top:30px; padding:12px; }

  .hidden { display:none !important; }
</style>
</head>
<body>
<div class="wrap">

  <header class="app-hd">
    <div class="brand">DUVETICA · 매출 리뷰</div>
    <div class="as-of" id="asof"></div>
  </header>

  <!-- SEASON HERO TAB - 최상단 대전제 -->
  <div class="season-hero" role="tablist">
    <div class="hero-tab active" data-season="26SS">
      <span class="label">26SS</span>
      <span class="sub">SPRING / SUMMER</span>
    </div>
    <div class="hero-tab" data-season="25FW">
      <span class="label">25FW</span>
      <span class="sub">FALL / WINTER</span>
    </div>
  </div>

  <!-- INSIGHTS -->
  <h2 class="sect">시즌 인사이트</h2>
  <div class="insight-row" id="insights"></div>

  <!-- 7-DAY TREND -->
  <h2 class="sect">최근 7일 시즌 매출 추이</h2>
  <div class="trend">
    <div class="trend-bars" id="trend"></div>
  </div>

  <!-- YESTERDAY TOP -->
  <h2 class="sect">전일(<span id="ydt"></span>) 시즌 BEST</h2>
  <div id="yt-wrap"></div>

  <!-- SEASON BEST SELLER -->
  <h2 class="sect">시즌 BEST SELLER TOP 20</h2>
  <div class="stabs">
    <div class="stab active" data-metric="amt">판매금액</div>
    <div class="stab" data-metric="qty">판매수량</div>
  </div>

  <div class="season-summary" id="ssum"></div>
  <div class="grid" id="grid"></div>

  <!-- SHOPS -->
  <h2 class="sect">매장별 BEST SELLER (TOP 15)</h2>
  <div id="shops"></div>

  <footer>
    DCS AI · DUVETICA Sales Review<br/>
    base date: <span id="bdt"></span> · 데이터 출처: F&F 지식그래프
  </footer>

</div>

<script id="appdata" type="application/json">__DATA_PLACEHOLDER__</script>
<script>
(function(){
  var DATA = JSON.parse(document.getElementById('appdata').textContent);
  var state = { season: '26SS', metric: 'amt' };

  var SESN_CODE = { '26SS': '26S', '25FW': '25F' };

  function fmtWon(v){
    if (v == null) return '-';
    var n = +v;
    if (n >= 1e8) return (n/1e8).toFixed(2) + '억';
    if (n >= 1e4) return Math.round(n/1e4).toLocaleString() + '만';
    return Math.round(n).toLocaleString();
  }
  function fmtQty(v){ return (v||0).toLocaleString(); }
  function pct(v){ return Math.round((v||0)*100) + '%'; }

  function sesnPillCls(s){
    if (!s) return 'n';
    var l = s.charAt(s.length-1).toUpperCase();
    if (l === 'S') return 'ss';
    if (l === 'F') return 'fw';
    return 'n';
  }

  // Header static
  document.getElementById('asof').innerHTML = '기준일 ' + DATA.meta.base_dt + '<br/>생성 ' + DATA.meta.generated_at;
  document.getElementById('bdt').textContent = DATA.meta.base_dt;
  document.getElementById('ydt').textContent = DATA.meta.base_dt;

  function renderInsights(){
    var arr = DATA.seasons[state.season].insights || [];
    var wrap = document.getElementById('insights');
    wrap.innerHTML = '';
    arr.forEach(function(it){
      var el = document.createElement('div');
      el.className = 'insight';
      el.innerHTML =
        '<div class="t">' + it.title + '</div>' +
        '<div class="v">' + it.value + '</div>' +
        '<div class="d ' + (it.tone||'neutral') + '">' +
          (it.delta ? '<span class="delta">' + it.delta + '</span>' : '') +
          '<span class="desc">' + (it.desc||'') + '</span>' +
        '</div>';
      wrap.appendChild(el);
    });
  }

  function renderTrend(){
    var sesn = SESN_CODE[state.season];
    var trend = DATA.daily.days;
    var wrap = document.getElementById('trend');
    wrap.innerHTML = '';
    var amts = trend.map(function(d){ return (d.by_sesn[sesn]||{}).amt || 0; });
    var maxAmt = Math.max.apply(null, amts) || 1;
    trend.forEach(function(d, idx){
      var amt = (d.by_sesn[sesn]||{}).amt || 0;
      var pctH = amt > 0 ? Math.max(4, (amt / maxAmt) * 100) : 4;
      var bar = document.createElement('div');
      bar.className = 'trend-bar' + (idx === trend.length - 1 ? ' today' : '') + (amt === 0 ? ' empty' : '');
      bar.innerHTML =
        '<div class="v">' + (amt > 0 ? fmtWon(amt) : '-') + '</div>' +
        '<div class="b" style="height:' + pctH + '%"></div>' +
        '<div class="lbl">' + d.label + '</div>';
      wrap.appendChild(bar);
    });
  }

  function renderYesterday(){
    var seasonObj = DATA.seasons[state.season];
    var arr = seasonObj.yesterday_top || [];
    var wrap = document.getElementById('yt-wrap');
    if (arr.length === 0) {
      wrap.innerHTML = '<div class="empty-state">전일 ' + state.season + ' 판매 데이터가 없습니다.</div>';
      return;
    }
    var rows = arr.map(function(s){
      return '<div class="row">' +
        '<div class="rk">' + s.rank + '</div>' +
        '<div class="ct">' +
          '<div class="n">' + (s.prdt_nm || '-') + '</div>' +
          '<div class="m">' + (s.item_nm || '') + ' · ' + (s.prdt_cd||'') + '</div>' +
        '</div>' +
        '<div class="vv">' +
          '<div class="a">' + fmtWon(s.amt) + '</div>' +
          '<div class="q">' + fmtQty(s.qty) + '수량</div>' +
        '</div>' +
      '</div>';
    }).join('');
    wrap.innerHTML = '<div class="yt">' + rows + '</div>';
  }

  function renderSeason(){
    var seasonObj = DATA.seasons[state.season];
    var list = state.metric === 'amt' ? seasonObj.top_amt : seasonObj.top_qty;
    var ssum = document.getElementById('ssum');
    ssum.innerHTML =
      '<span><b>' + state.season + '</b> · ' + (seasonObj.period_label||'') + '</span>' +
      '<span><b>' + fmtWon(seasonObj.total_amt) + '원</b> 누적</span>' +
      '<span><b>' + fmtQty(seasonObj.total_qty) + '</b>수량</span>' +
      '<span><b>' + seasonObj.style_count + '</b>스타일</span>';

    var grid = document.getElementById('grid');
    grid.innerHTML = '';
    list.forEach(function(s){
      var card = document.createElement('div');
      card.className = 'card';
      var imgPart = s.img
        ? '<img loading="lazy" src="' + s.img + '" alt="" onerror="this.parentNode.innerHTML=\'<span class=&quot;placeholder&quot;>이미지 없음</span>\'"/>'
        : '<span class="placeholder">이미지 없음</span>';
      var crown = s.rank === 1 ? '<span class="crown">👑</span>' : '';
      var sr = s.sale_rt || 0;

      // Color breakdown
      var colors = s.colors || [];
      var maxCQty = colors.length ? Math.max.apply(null, colors.map(function(c){ return c.qty || 0; })) || 1 : 1;
      var colorRows = colors.map(function(c){
        var w = (c.qty / maxCQty) * 100;
        return '<div class="crow">' +
          '<span class="ccd">' + c.color_cd + '</span>' +
          '<span class="cbar"><i style="width:' + w + '%"></i></span>' +
          '<span class="cqty"><b>' + fmtQty(c.qty) + '</b>수량</span>' +
        '</div>';
      }).join('');
      var colorBlock = colors.length > 0
        ? '<div class="colors"><div class="colors-hd">컬러별 판매수량 (' + colors.length + '컬러)</div>' +
          '<div class="clist">' + colorRows + '</div></div>'
        : '';

      card.innerHTML =
        '<div class="imgwrap">' + imgPart +
          '<span class="rank">#' + s.rank + '</span>' + crown +
        '</div>' +
        '<div class="body">' +
          '<div class="nm">' + (s.prdt_nm || '-') + '</div>' +
          '<div class="meta">' +
            '<span class="badge">' + (s.item_group || '') + '</span>' +
            '<span class="badge">TAG ' + fmtWon(s.tag_price) + '원</span>' +
          '</div>' +
          '<div class="stats">' +
            '<div>' +
              '<div class="amt">' + fmtWon(s.sale_amt) + '원</div>' +
              '<div class="qty">' + fmtQty(s.sale_qty) + '수량 / 입고 ' + fmtQty(s.stor_qty) + '</div>' +
            '</div>' +
          '</div>' +
          '<div class="salert">판매율 ' + pct(sr) +
            '<span class="bar"><i style="width:' + Math.min(100, sr*100) + '%"></i></span>' +
          '</div>' +
          colorBlock +
        '</div>';
      grid.appendChild(card);
    });
  }

  function renderShops(){
    var seasonObj = DATA.seasons[state.season];
    var wrap = document.getElementById('shops');
    wrap.innerHTML = '';
    if (!seasonObj.shops || seasonObj.shops.length === 0) {
      wrap.innerHTML = '<div class="empty-state">매장 데이터 없음</div>';
      return;
    }
    seasonObj.shops.forEach(function(sh, idx){
      var d = document.createElement('details');
      d.className = 'shop';
      var styleRows = sh.styles.map(function(st, j){
        return '<div class="style-row">' +
          '<div class="sr">' + (j+1) + '</div>' +
          '<div class="sn">' + (st.prdt_nm||'-') +
            '<div class="si">' + (st.item_nm||'') + '</div>' +
          '</div>' +
          '<div class="sa">' + fmtWon(st.amt) + '원' +
            '<div class="sq">' + fmtQty(st.qty) + '수량</div>' +
          '</div>' +
        '</div>';
      }).join('');
      d.innerHTML =
        '<summary>' +
          '<div class="rank-circle">' + (idx+1) + '</div>' +
          '<div class="info">' +
            '<div class="nm">' + (sh.shop_nm||'-') + '</div>' +
            '<div class="sub">' + (sh.area||'') + ' · ' + (sh.channel||'') + (sh.online ? ' · ' + sh.online : '') + '</div>' +
          '</div>' +
          '<div class="right">' +
            '<div class="a">' + fmtWon(sh.amt) + '원</div>' +
            '<div class="q">' + fmtQty(sh.qty) + '수량</div>' +
          '</div>' +
          '<span class="chev">▾</span>' +
        '</summary>' +
        '<div class="styles">' + styleRows + '</div>';
      wrap.appendChild(d);
    });
  }

  function renderAll(){
    renderInsights();
    renderTrend();
    renderYesterday();
    renderSeason();
    renderShops();
  }

  // Season tabs (top-level)
  document.querySelectorAll('.hero-tab').forEach(function(t){
    t.addEventListener('click', function(){
      document.querySelectorAll('.hero-tab').forEach(function(x){ x.classList.remove('active'); });
      t.classList.add('active');
      state.season = t.dataset.season;
      renderAll();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
  // Metric sub-tabs
  document.querySelectorAll('.stab').forEach(function(t){
    t.addEventListener('click', function(){
      document.querySelectorAll('.stab').forEach(function(x){ x.classList.remove('active'); });
      t.classList.add('active');
      state.metric = t.dataset.metric;
      renderSeason();
    });
  });

  renderAll();
})();
</script>
</body>
</html>
"""


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    data_text = json.dumps(data, ensure_ascii=False)
    data_text = data_text.replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_text)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_ROOT.write_text(html, encoding="utf-8")
    HTML_OUTPUT.write_text(html, encoding="utf-8")
    size_kb = HTML_ROOT.stat().st_size / 1024
    print(f"HTML written: {HTML_ROOT} ({size_kb:.1f} KB)")
    print(f"HTML mirrored: {HTML_OUTPUT}")


if __name__ == "__main__":
    main()
