#!/usr/bin/env python3
"""從 state/ 與 drivers/ 產生 docs/index.html — GitHub Pages 的公開門面。

用法:
    python scripts/build_site.py

設計原則:

**單向產生，絕不手改。** 與 reports/INDEX.md 同一性質：docs/index.html 是輸出不是輸入。
手改它會在下次執行時被覆蓋，且 CI 會擋下不一致的提交。

**自我包含，不依賴 CDN。** 不引用外部字型、CSS、JS。GitHub Pages 雖然不像 Artifact
有 CSP 限制，但外部依賴會讓頁面在別人 fork 之後悄悄壞掉，也讓「這頁到底載入了什麼」
變成一個需要查證的問題。字型一律用系統堆疊。

**輸出必須是決定性的。** 不嵌入建置時間戳、不讀 git log（CI 的 shallow clone 只有一個
commit，git log 會產生不同結果而讓 freshness 檢查誤判）。時間軸改由 reports 的
front-matter 與 driver 的 event_log 組成 —— 那本來就是研究記錄，比 commit log 更貼題。

**不輸出任何倉位資訊。** 沒有配置圓餅圖、沒有權重長條、沒有損益曲線。頁面只呈現
state 與 drivers 裡已經存在的欄位。產生後仍會被 check_public.py 掃描（.html 已納入）。
"""
import datetime
import glob
import html
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML： pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "index.html")
PLACEHOLDER = "__"

SIGNAL_CLASS = {"偏多": "sig-long", "中性": "sig-flat", "偏空": "sig-short"}


def is_blank(v):
    return v is None or v == PLACEHOLDER or (isinstance(v, str) and v.strip("_ ") == "")


def clean(v):
    """把 __ 佔位符換成 None（前端統一顯示為「未填」），並把日期轉成字串。

    PyYAML 會把未加引號的 2026-08-27 解析成 datetime.date，那不能 JSON 序列化；
    而 state 裡的日期有些加引號（'2026-11'）有些沒有，兩種都會出現。
    """
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return None if is_blank(v) else v


def load_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def front_matter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def collect():
    tickers, drivers, reports = [], [], []

    for path in sorted(glob.glob(os.path.join(ROOT, "state", "*.yaml"))):
        base = os.path.basename(path)
        if base.startswith("_") or base == "coverage.yaml":
            continue
        d = load_yaml(path)
        if isinstance(d, dict):
            d = clean(d)
            # 台股代號未加引號時 YAML 會解析成整數（3324 而非 "3324"），
            # 但報告 front-matter 用的是字串。型別不一致不會讓頁面壞掉，
            # 卻會讓任何想把 tickers 與 reports 對起來的程式安靜失敗。
            d["ticker"] = str(d.get("ticker", ""))
            tickers.append(d)

    cov = clean(load_yaml(os.path.join(ROOT, "state", "coverage.yaml")))

    for path in sorted(glob.glob(os.path.join(ROOT, "drivers", "*.yaml"))):
        if os.path.basename(path).startswith("_"):
            continue
        d = load_yaml(path)
        if isinstance(d, dict):
            drivers.append(clean(d))

    for path in sorted(glob.glob(os.path.join(ROOT, "reports", "**", "*.md"), recursive=True)):
        if os.path.basename(path) == "INDEX.md":
            continue
        fm = front_matter(path)
        if not fm:
            continue
        reports.append({
            "date": str(fm.get("date", "")),
            "ticker": str(fm.get("ticker", "")),
            "name": str(fm.get("name", "")),
            "level": str(fm.get("level", "")),
            "summary": str(fm.get("summary", "")),
            "signal": str(fm.get("signal", "")),
            "tp_after": fm.get("tp_after"),
            "path": os.path.relpath(path, ROOT).replace(os.sep, "/"),
        })
    reports.sort(key=lambda r: r["date"], reverse=True)

    # 時間軸 = 報告 + driver 的 event_log。兩者都是研究記錄，不用 git log。
    timeline = [{
        "date": r["date"], "kind": "report", "ticker": r["ticker"],
        "level": r["level"], "text": r["summary"], "path": r["path"],
    } for r in reports]

    for dv in drivers:
        for ev in (dv.get("event_log") or []):
            if not isinstance(ev, dict):
                continue
            timeline.append({
                "date": str(ev.get("date", "")), "kind": "driver",
                "ticker": dv.get("id", ""), "level": "driver",
                "text": str(ev.get("summary", "")), "path": None,
            })
    timeline.sort(key=lambda x: (x["date"], x["kind"]), reverse=True)

    return {"tickers": tickers, "coverage": cov, "drivers": drivers,
            "reports": reports, "timeline": timeline}


CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#0a0908; --panel:#141210; --panel2:#1c1917; --line:#2b2724;
  --ink:#e8e3dc; --muted:#9a9188; --dim:#6b635c;
  --gold:#c9a449; --long:#e05252; --short:#3fa87a; --flat:#8a827a;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Songti TC","Noto Serif CJK TC",serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif;
  line-height:1.65;font-size:15px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 80px}
h1,h2,h3{font-family:var(--serif);font-weight:600;letter-spacing:.01em;line-height:1.25}
h1{font-size:clamp(28px,5vw,42px);margin:0 0 8px}
h2{font-size:clamp(20px,3vw,26px);margin:56px 0 6px;color:var(--gold)}
h3{font-size:17px;margin:0}
a{color:var(--gold)}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.sub{color:var(--muted);font-size:14px;margin:0}
.dim{color:var(--dim)}
header{border-bottom:1px solid var(--line);padding:48px 0 28px;margin-bottom:8px}
.lede{color:var(--muted);max-width:70ch;margin:14px 0 0}
.disc{margin:22px 0 0;padding:14px 16px;border-left:3px solid var(--gold);
  background:var(--panel);color:var(--muted);font-size:13.5px;border-radius:0 6px 6px 0}
.disc strong{color:var(--ink)}
.secnote{color:var(--muted);font-size:14px;margin:0 0 20px;max-width:74ch}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(330px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.card-hd{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:4px}
.tk{font-family:var(--mono);font-size:19px;color:var(--gold);font-weight:600}
.nm{color:var(--muted);font-size:13px}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;
  font-weight:600;border:1px solid currentColor;white-space:nowrap}
.sig-long{color:var(--long)}.sig-short{color:var(--short)}.sig-flat{color:var(--flat)}
.tags{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0 12px}
.tag{font-family:var(--mono);font-size:11px;color:var(--dim);
  border:1px solid var(--line);border-radius:4px;padding:1px 6px}
.thesis{font-size:14px;color:var(--ink);margin:0 0 14px;padding-left:11px;border-left:2px solid var(--line)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 14px;font-size:13px;margin:0 0 12px}
.kv dt{color:var(--muted)}
.kv dd{margin:0;font-family:var(--mono);text-align:right}
.pbar{display:flex;height:7px;border-radius:4px;overflow:hidden;margin:12px 0 6px;background:var(--panel2)}
.pbar i{display:block}
.pbar .b{background:var(--short)}.pbar .m{background:var(--flat)}.pbar .u{background:var(--long)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:right;padding:5px 6px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:500;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}
td.n{font-family:var(--mono);font-variant-numeric:tabular-nums}
details{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
summary{cursor:pointer;color:var(--muted);font-size:12.5px;list-style:none;user-select:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸ ";color:var(--gold)}
details[open]>summary::before{content:"▾ "}
details>div{padding-top:10px}
.ok{color:var(--short)}.warn{color:var(--gold)}.bad{color:var(--long)}
.fx{font-size:12.5px;margin:0 0 9px;padding-left:11px;border-left:2px solid var(--line)}
.fx b{font-weight:600}
.scroll{overflow-x:auto}
.tl{list-style:none;padding:0;margin:0;border-left:1px solid var(--line)}
.tl li{position:relative;padding:0 0 20px 22px}
.tl li::before{content:"";position:absolute;left:-4.5px;top:8px;width:8px;height:8px;
  border-radius:50%;background:var(--gold)}
.tl li.driver::before{background:var(--flat)}
.tl .d{font-family:var(--mono);font-size:12px;color:var(--dim)}
.tl .t{font-size:14px;margin:2px 0 0}
.tl .m{font-size:12px;color:var(--muted);margin-top:2px}
.lvl{font-family:var(--mono);font-size:11px;border:1px solid var(--line);
  border-radius:4px;padding:0 5px;color:var(--muted);margin-left:6px}
.prem{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--gold);
  border-radius:0 8px 8px 0;padding:16px 18px;margin:0 0 16px}
footer{margin-top:72px;padding-top:22px;border-top:1px solid var(--line);
  color:var(--dim);font-size:12.5px}
@media (max-width:560px){.kv dd{text-align:left}.grid{grid-template-columns:1fr}}
"""


def esc(v):
    return html.escape("" if v is None else str(v))


def build_html(data):
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=None,
                         separators=(",", ":"))
    as_of = esc((data.get("coverage") or {}).get("as_of", ""))
    n_tick = len(data["tickers"])
    n_rep = len(data["reports"])
    n_drv = len(data["drivers"])

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CTA 推論專案｜個股研究覆蓋</title>
<meta name="description" content="增量式個股研究倉庫的公開檢視介面。不含任何倉位資訊。">
<meta name="robots" content="index,follow">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>CTA 推論專案</h1>
  <p class="sub num">as_of {as_of} ｜ 覆蓋 {n_tick} 檔 ｜ 驅動因子 {n_drv} 個 ｜ 推論文件 {n_rep} 份</p>
  <p class="lede">
    增量式個股研究倉庫。每則新資訊只產生一份差分推論，不重建整份報告。
    本頁由 <span class="num">scripts/build_site.py</span> 自 <span class="num">state/</span> 與
    <span class="num">drivers/</span> 直接產生，是輸出不是輸入 —— 內容永遠與倉庫一致。
  </p>
  <div class="disc">
    <strong>本倉庫不含任何倉位資訊。</strong>
    沒有成本、張數、配置比重、Kelly、損益，也不揭露作者是否持有任何標的。
    追蹤清單是<strong>研究覆蓋範圍</strong>，不是持有清單；因子分布以等權為基準，
    那是清單的結構描述，與任何實際配置無關。
    訊號評級（偏多／中性／偏空）是<strong>研究結論，不是交易建議</strong>。
    本頁所有內容僅供研究記錄與自我校準，非投資建議。
  </div>
</header>

<h2>覆蓋清單</h2>
<p class="secnote">
  每張卡片是該標的當下的最佳判斷（<span class="num">state/&lt;ticker&gt;.yaml</span>）。
  情境機率合計恆為 1.00。顏色沿用台股慣例：<span class="sig-long">紅＝偏多</span>、
  <span class="sig-flat">灰＝中性</span>、<span class="sig-short">綠＝偏空</span>。
</p>
<div class="grid" id="tickers"></div>

<h2>共用驅動因子</h2>
<p class="secnote">
  跨標的變數的唯一真實來源。一個共用事實只能有一個家 —— 個股用
  <span class="num">driver_refs</span> 引用，絕不複製數值。
  同一則消息對硬體端與平台端的方向常常相反，逐檔記在 <span class="num">transmission</span>。
</p>
<div class="grid" id="drivers"></div>

<h2>覆蓋層</h2>
<div id="coverage"></div>

<h2>更新時間軸</h2>
<p class="secnote">
  由推論文件的 front-matter 與驅動因子的 event_log 組成 —— 那是研究記錄本身。
  報告是 append-only：判斷錯了寫新報告修正，舊的留在原地。
</p>
<ul class="tl" id="timeline"></ul>

<footer>
  <p>
    原始碼與完整推論記錄：<a href="https://github.com/mark00lui/CTA_report">github.com/mark00lui/CTA_report</a>
    ｜本頁自動產生，請勿手改。
  </p>
  <p>
    免責：本專案為公開研究記錄，非投資建議。作者不揭露任何持倉資訊，
    讀者不應假設作者持有或不持有任何標的。
  </p>
</footer>

</div>
<script id="data" type="application/json">{payload}</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const SC = {{'偏多':'sig-long','中性':'sig-flat','偏空':'sig-short'}};
const E = s => String(s ?? '').replace(/[&<>"']/g, c => (
  {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
const n = v => (v === null || v === undefined || v === '') ? '<span class="dim">未填</span>' : E(v);
const pct = p => (p === null || p === undefined) ? 0 : Math.round(p * 100);

function fxState(s) {{
  if (s === '未觸發') return '<span class="ok">未觸發</span>';
  if (s === '已觸發') return '<span class="bad">已觸發</span>';
  return '<span class="warn">' + E(s || '未驗證') + '</span>';
}}

function scenTable(sc) {{
  if (!sc) return '';
  const rows = ['bear','base','bull'].map(k => {{
    const s = sc[k] || {{}};
    const lbl = {{bear:'Bear',base:'Base',bull:'Bull'}}[k];
    return `<tr><td>${{lbl}}</td><td class="n">${{s.p !== null && s.p !== undefined ? pct(s.p)+'%' : '—'}}</td>
      <td class="n">${{n(s.eps)}}</td><td class="n">${{s.exit_multiple ? E(s.exit_multiple)+'x' : '—'}}</td>
      <td class="n">${{n(s.tp)}}</td></tr>`;
  }}).join('');
  const b = pct(sc.bear?.p), m = pct(sc.base?.p), u = pct(sc.bull?.p);
  const bar = (b+m+u) > 0
    ? `<div class="pbar" title="Bear ${{b}}% / Base ${{m}}% / Bull ${{u}}%">
         <i class="b" style="width:${{b}}%"></i><i class="m" style="width:${{m}}%"></i><i class="u" style="width:${{u}}%"></i></div>` : '';
  return bar + `<div class="scroll"><table><thead><tr><th>情境</th><th>機率</th><th>EPS</th><th>倍數</th><th>目標價</th></tr></thead><tbody>${{rows}}</tbody></table></div>`;
}}

document.getElementById('tickers').innerHTML = D.tickers.map(t => {{
  const sig = t.signal || {{}};
  const cls = SC[sig.rating] || 'sig-flat';
  const sc = t.scenarios || {{}};
  const cta = t.cta || {{}};
  const kvs = (t.key_variables || []).map(k =>
    `<tr><td>${{E(k.name)}}</td><td class="n">${{n(k.value)}}${{k.unit && k.value !== null ? ' <span class="dim">'+E(k.unit)+'</span>' : ''}}</td><td class="dim">${{E(k.tier || '')}}</td></tr>`).join('');
  const fxs = (t.falsifiers || []).map(f =>
    `<p class="fx"><b>${{fxState(f.status)}}</b> ${{E(f.condition)}}<br><span class="dim num">check_by ${{E(f.check_by || '未定')}}</span></p>`).join('');
  const refs = (t.driver_refs || []).map(r =>
    `<span class="tag">${{E(r.driver)}} ${{E(r.direction || '')}}</span>`).join(' ');
  return `<article class="card">
    <div class="card-hd"><div><span class="tk">${{E(t.ticker)}}</span> <span class="nm">${{E(t.name)}}</span></div>
      <span class="badge ${{cls}}">${{E(sig.rating || '未評級')}}</span></div>
    <div class="tags">${{(t.factor_tags||[]).map(x=>`<span class="tag">${{E(x)}}</span>`).join('')}}</div>
    <p class="thesis">${{t.thesis ? E(t.thesis) : '<span class="dim">論點尚未寫定</span>'}}</p>
    <dl class="kv">
      <dt>加權目標價</dt><dd>${{n(sc.weighted_tp)}}</dd>
      <dt>現價</dt><dd>${{n(cta.price)}}</dd>
      <dt>基準年</dt><dd>${{n(t.valuation_base_year)}}</dd>
      <dt>信心度</dt><dd>${{n(sig.conviction)}}</dd>
      <dt>更新</dt><dd>${{n(t.last_updated)}}</dd>
    </dl>
    ${{scenTable(sc)}}
    ${{refs ? `<div class="tags" style="margin-top:12px">${{refs}}</div>` : ''}}
    <details><summary>關鍵變數（${{(t.key_variables||[]).length}}）</summary><div class="scroll">
      <table><thead><tr><th>變數</th><th>值</th><th>tier</th></tr></thead><tbody>${{kvs}}</tbody></table></div></details>
    <details><summary>否證點（${{(t.falsifiers||[]).length}}）</summary><div>${{fxs}}</div></details>
    <details><summary>CTA 位階與訊號依據</summary><div>
      <dl class="kv"><dt>位階</dt><dd style="text-align:left">${{n(cta['位階'])}}</dd>
      <dt>關鍵均線</dt><dd>${{n(cta.key_ma)}}</dd>
      <dt>支撐</dt><dd>${{n(cta.support)}}</dd>
      <dt>壓力</dt><dd>${{n(cta.resistance)}}</dd>
      <dt>失效價位</dt><dd style="text-align:left">${{n(cta.invalidation)}}</dd></dl>
      <p class="fx">${{n(sig.basis)}}</p>
      <p class="fx"><b>改變條件</b><br>${{n(sig.changes_if)}}</p></div></details>
  </article>`;
}}).join('');

document.getElementById('drivers').innerHTML = D.drivers.map(d => {{
  const c = d.current || {{}};
  const comps = (d.components || []).map(x =>
    `<tr><td>${{E(x.name)}}</td><td class="n">${{n(x.value)}}</td><td class="dim">${{E(x.guidance || '')}}</td></tr>`).join('');
  const tr = (d.transmission || []).map(x =>
    `<tr><td class="num">${{E(x.ticker)}}</td><td class="n ${{x.direction==='+'?'sig-long':'sig-short'}}">${{E(x.direction)}}</td>
     <td class="dim" style="text-align:left">${{E(x.lag)}}</td></tr>`).join('');
  const fxs = (d.falsifiers || []).map(f =>
    `<p class="fx"><b>${{fxState(f.status)}}</b> ${{E(f.condition)}}<br><span class="dim num">check_by ${{E(f.check_by || '未定')}}</span></p>`).join('');
  return `<article class="card">
    <div class="card-hd"><div><span class="tk">${{E(d.id)}}</span></div>
      <span class="badge sig-flat">driver</span></div>
    <p class="thesis">${{E(d.what_it_is)}}</p>
    <dl class="kv">
      <dt>現值</dt><dd>${{n(c.value)}}</dd>
      <dt>單位</dt><dd style="text-align:left">${{n(c.unit)}}</dd>
      <dt>tier</dt><dd>${{n(c.tier)}}</dd>
      <dt>as_of</dt><dd>${{n(c.as_of)}}</dd>
      <dt>更新頻率</dt><dd style="text-align:left">${{n(d.update_cadence)}}</dd>
    </dl>
    <details><summary>成分（${{(d.components||[]).length}}）</summary><div class="scroll">
      <table><thead><tr><th>成分</th><th>值</th><th>guidance</th></tr></thead><tbody>${{comps}}</tbody></table></div></details>
    <details><summary>傳導對象（${{(d.transmission||[]).length}}）</summary><div class="scroll">
      <table><thead><tr><th>標的</th><th>方向</th><th>時滯</th></tr></thead><tbody>${{tr}}</tbody></table></div></details>
    <details><summary>否證點（${{(d.falsifiers||[]).length}}）</summary><div>${{fxs}}</div></details>
  </article>`;
}}).join('');

const cov = D.coverage || {{}};
const mix = cov.equal_weight_factor_mix || {{}};
const sf = cov.shared_falsifier || {{}};
document.getElementById('coverage').innerHTML = `
  <div class="prem"><h3>共同前提</h3>
    <p class="sub" style="margin-top:6px">${{E(cov.common_premise)}}</p></div>
  <div class="prem"><h3>共用否證點</h3>
    <p class="sub" style="margin-top:6px">${{fxState(sf.status)}} ${{E(sf.condition)}}</p>
    <p class="sub dim" style="margin-top:4px">觸發後：${{E(sf.action)}}</p></div>
  <div class="card"><h3 style="margin-bottom:10px">等權基準下的因子分布</h3>
    <p class="sub dim" style="margin:0 0 10px">這是覆蓋清單的結構描述，與任何實際配置無關。</p>
    <div class="scroll"><table><thead><tr><th>因子</th><th>檔數</th><th>等權占比</th><th>說明</th></tr></thead><tbody>
    ${{Object.entries(mix).map(([k,v]) =>
      `<tr><td class="num">${{E(k)}}</td><td class="n">${{E(v.count)}}</td><td class="n">${{E(v.pct)}}%</td>
       <td class="dim" style="text-align:left">${{E(v.note || '')}}</td></tr>`).join('')}}
    </tbody></table></div></div>`;

document.getElementById('timeline').innerHTML = D.timeline.map(e => `
  <li class="${{e.kind}}">
    <div class="d">${{E(e.date)}}</div>
    <p class="t">${{e.path ? `<a href="https://github.com/mark00lui/CTA_report/blob/main/${{E(e.path)}}">${{E(e.ticker)}}</a>` : E(e.ticker)}}
      <span class="lvl">${{E(e.level)}}</span></p>
    <p class="m">${{E(e.text)}}</p>
  </li>`).join('');
</script>
</body>
</html>
"""


def main():
    data = collect()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_html(data))
    print(f"已產生 docs/index.html — 覆蓋 {len(data['tickers'])} 檔、"
          f"driver {len(data['drivers'])} 個、報告 {len(data['reports'])} 份、"
          f"時間軸 {len(data['timeline'])} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
