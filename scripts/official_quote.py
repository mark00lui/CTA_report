#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""台股官方報價與技術面 —— 一次取齊，免帳號、一手。

存在的理由是 2026-09-12 那一批修正：上櫃標的在 `stockanalysis.com` 全部 404
（9／9 實測），只能退而用第三方頁面，而代價是 5 檔的價格過期或日期錯位。
其中 3131 的 `cta.price` 被一個**盤中值**取代了一個正確的收盤價，
而取代它的理由本身也是錯的 —— 那次推論內部完全自洽，三個數字互相印證，一起平移了一個交易日。

⚠⚠⚠ **內部自洽的錯誤過不了任何內部檢查。唯一抓得到它的是一個外部的、帶完整日期的序列
—— 亦即交易所自己。這支腳本就是那個序列。**

用法：
    python scripts/official_quote.py 3131
    python scripts/official_quote.py 3131 --months 12   # 要算 MA120／MA240 時
    python scripts/official_quote.py 2308 3017 6442     # 一次多檔

輸出：最新收盤與其日期、ATR20、MA5/10/20/60(/120/240)、區間高低、官方本益比／股價淨值比／殖利率，
並對每條均線直接判定它能不能當 `invalidation`（雙邊規則）。

⚠ 只支援台股。美股的官方對應物是 SEC（data.sec.gov）與財政部，見
  .claude/skills/cta-research/references/forward-estimates.md 的「美股的官方通道」。

實作上的兩個坑（踩過才知道）：
  1. ⚠ **Python 的 `urllib`／`requests` 對 `tpex.org.tw` 憑證驗證失敗**
     （`SSLCertVerificationError: Missing Subject Key Identifier`），而 `curl` 接受。
     → 本腳本一律用 `curl` 抓成檔案再讀。
  2. ⚠ **日期是民國年**：`1150911` ＝ 2026-09-11。
"""
import argparse
import io
import json
import os
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

CACHE = os.path.join(tempfile.gettempdir(), "cta_official_quote")
TWSE_DAY = ("https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
            "?date=%s01&stockNo=%s&response=json")
TPEX_DAY = ("https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock"
            "?code=%s&date=%s/%s/01&id=&response=json")
TWSE_ALL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TPEX_ALL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
TWSE_BWIBBU = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"
TPEX_PERATIO = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis"

# 雙邊規則（2026-09-12 由 3131 釐清）：兩個界擋不同的失效模式，必須同時通過。
ATR_MIN_RATIO = 2.0    # 下界：均線離價格太近時，「站上／跌破」與雜訊分不開
MAX_DISTANCE = 0.20    # 上界：離價格太遠的均線不構成有意義的失效點


def curl_json(url, name, refresh=False):
    if not os.path.isdir(CACHE):
        os.makedirs(CACHE)
    path = os.path.join(CACHE, name)
    if refresh or not os.path.exists(path) or os.path.getsize(path) < 40:
        subprocess.run(["curl", "-s", "--max-time", "45", url, "-o", path], check=True)
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def roc_to_iso(roc):
    """115/09/11 -> 2026-09-11"""
    y, m, d = roc.split("/")
    return "%d-%s-%s" % (int(y) + 1911, m, d)


def num(x):
    try:
        return float(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def month_list(n):
    """回傳最近 n 個月的 (YYYY, MM)，以今天為準往回數。"""
    # ⚠ 不用 datetime.now() 取「今天」會讓輸出不可複現；這裡刻意讀系統日期，
    #   因為本腳本的用途就是取「當下」的官方資料。
    import datetime
    t = datetime.date.today()
    out = []
    y, m = t.year, t.month
    for _ in range(n):
        out.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


def detect_market(tk):
    tpex = curl_json(TPEX_ALL, "tpex_all.json")
    if tpex and any(r.get("SecuritiesCompanyCode") == tk for r in tpex):
        return "上櫃"
    twse = curl_json(TWSE_ALL, "twse_all.json")
    if twse and any(r.get("Code") == tk for r in twse):
        return "上市"
    return None


SKIPPED = []


def bars(tk, market, months):
    """回傳 [(iso_date, open, high, low, close)]，依日期遞增。
    ⚠ 無法解析 OHLC 的列（零成交日）會被記進 SKIPPED 並在輸出中報告，不靜默丟棄。"""
    out = []
    for y, m in month_list(months):
        if market == "上櫃":
            url = TPEX_DAY % (tk, y, "%02d" % m)
            d = curl_json(url, "%s_%d%02d_otc.json" % (tk, y, m))
            rows = ((d or {}).get("tables") or [{}])[0].get("data") or []
        else:
            url = TWSE_DAY % ("%d%02d" % (y, m), tk)
            d = curl_json(url, "%s_%d%02d_twse.json" % (tk, y, m))
            rows = (d or {}).get("data") or []
        for r in rows:
            o, h, l, c = num(r[3]), num(r[4]), num(r[5]), num(r[6])
            if None not in (o, h, l, c):
                out.append((roc_to_iso(r[0]), o, h, l, c))
            else:
                # ⚠ 2026-09-12（3665 實測）：零成交日的 OHLC 是 "--"，初版靜默跳過，
                #   結果根數少一根而長均線窗口往前多含一天 —— 使用者看不到這件事發生。
                #   零成交通常代表暫停交易，那本身是 CTA 相關的事實，必須報出來。
                SKIPPED.append((roc_to_iso(r[0]), r[1], r[2]))
    out.sort(key=lambda x: x[0])
    return out


def valuation(tk, market):
    if market == "上櫃":
        d = curl_json(TPEX_PERATIO, "tpex_pe.json") or []
        for r in d:
            if r.get("SecuritiesCompanyCode") == tk:
                return {"本益比": r.get("PriceEarningRatio"),
                        "股價淨值比": r.get("PriceBookRatio"),
                        "殖利率": r.get("YieldRatio"),
                        "每股股利": r.get("DividendPerShare"),
                        "日期": roc_to_iso("%s/%s/%s" % (r["Date"][:3], r["Date"][3:5], r["Date"][5:]))}
    else:
        d = curl_json(TWSE_BWIBBU, "twse_pe.json") or []
        for r in d:
            if r.get("Code") == tk:
                return {"本益比": r.get("PEratio"),
                        "股價淨值比": r.get("PBratio"),
                        "殖利率": r.get("DividendYield"),
                        "日期": roc_to_iso("%s/%s/%s" % (r["Date"][:3], r["Date"][3:5], r["Date"][5:]))}
    return None


def atr(b, n=20):
    if len(b) < n + 1:
        return None
    trs = []
    for i in range(1, len(b)):
        _, _, h, l, c = b[i]
        pc = b[i - 1][4]
        trs.append(max(h - l, abs(h - pc), abs(pc - l)))
    return sum(trs[-n:]) / float(n)


def report(tk, months, refresh):
    market = detect_market(tk)
    if market is None:
        print("%s：兩個市場的日收盤清單都找不到這個代號 —— 確認它是否仍在交易" % tk)
        return
    b = bars(tk, market, months)
    if len(b) < 21:
        print("%s（%s）：只取到 %d 根，不足以算 ATR20" % (tk, market, len(b)))
        return
    px = b[-1][4]
    a = atr(b)
    hi = max(x[2] for x in b)
    lo = min(x[3] for x in b)
    hid = [x[0] for x in b if x[2] == hi][0]
    lod = [x[0] for x in b if x[3] == lo][0]

    print("=" * 66)
    print("%s（%s）  官方收盤 %.2f  日期 %s  共 %d 根（%s ~ %s）"
          % (tk, market, px, b[-1][0], len(b), b[0][0], b[-1][0]))
    print("=" * 66)
    if SKIPPED:
        print("⚠⚠ 有 %d 個交易日無法解析 OHLC（零成交，通常代表暫停交易）——"
              " 它們不在上面的根數裡，所以長均線的窗口會往前多含同樣天數：" % len(SKIPPED))
        for d0, vol, amt in SKIPPED:
            print("   %s  成交股數 %s  成交金額 %s" % (d0, vol, amt))
        print()
    print("當日 開 %.2f  高 %.2f  低 %.2f  收 %.2f" % (b[-1][1], b[-1][2], b[-1][3], px))
    print("ATR20 %.2f ＝ 收盤的 %.2f%%" % (a, a / px * 100))
    print("當日振幅 %.2f%%（＝ ATR 的 %.2f 倍）⚠ 單日振幅不得當門檻分母，偏誤方向不固定"
          % ((b[-1][2] - b[-1][3]) / px * 100, (b[-1][2] - b[-1][3]) / a))
    print()
    print("區間高 %.2f（%s）  區間低 %.2f（%s）  高低比 %.2f 倍" % (hi, hid, lo, lod, hi / lo))
    print("現價距區間高 %+.2f%%   在區間低之上 %+.2f%%" % ((px / hi - 1) * 100, (px / lo - 1) * 100))
    # ⚠ 雙邊規則對非均線位階同樣適用 —— 初版只檢下界，3211 實測漏掉上界（區間低距現價 23.07%）。
    d_lo = (px - lo) / px
    r_lo = d_lo / (a / px)
    if r_lo >= ATR_MIN_RATIO and d_lo <= MAX_DISTANCE:
        verd_lo = "✓ 可作 invalidation 候選（在價格下方）"
    elif r_lo < ATR_MIN_RATIO:
        verd_lo = "✗ 未過 2 倍下界"
    else:
        verd_lo = "✗ 超出 ±20% 上界"
    print("區間低距現價 %.2f%% ＝ %.2f 倍 ATR   %s" % (d_lo * 100, r_lo, verd_lo))
    # ⚠ 2026-09-12（2308 實測）：上面的「區間」是抓到多少根就算多少根，不等於 52 週。
    #   --months 14 給的是約 13.4 個月，而 2308 的最低點剛好落在窗口第一天（窗口外的一天）——
    #   把它寫成「52 週低」會錯 1.8%（821 對 556 差 48%）。所以另外算一個真正的 52 週。
    cutoff = "%04d-%02d-%02d" % (int(b[-1][0][:4]) - 1, int(b[-1][0][5:7]), int(b[-1][0][8:10]))
    w52 = [x for x in b if x[0] >= cutoff]
    if len(w52) >= 200 and w52[0][0] > b[0][0]:
        h52 = max(x[2] for x in w52)
        l52 = min(x[3] for x in w52)
        d52 = (px - l52) / px
        print("真 52 週（自 %s，%d 根）高 %.2f（%s）低 %.2f（%s）高低比 %.2f 倍；"
              "低距現價 %.2f%% ＝ %.2f 倍 ATR"
              % (cutoff, len(w52), h52, [x[0] for x in w52 if x[2] == h52][0],
                 l52, [x[0] for x in w52 if x[3] == l52][0], h52 / l52,
                 d52 * 100, d52 / (a / px)))
    elif len(w52) >= 200:
        print("真 52 週：窗口起點即資料起點，上面的區間就是 52 週（未被截斷）")
    print()
    c = [x[4] for x in b]
    print("均線                 值    價格相對位置   距現價    倍 ATR   判定（⚠ 方向決定它是哪一種）")
    for n in (5, 10, 20, 60, 120, 240):
        if len(c) < n:
            print("MA%-4d  （需 %d 根，目前 %d 根 —— 加 --months 取更多）" % (n, n, len(c)))
            continue
        ma = sum(c[-n:]) / float(n)
        rel = px / ma - 1.0               # 價格相對均線
        dist = abs(ma - px) / px         # 距現價（分母是價格，與 state 的慣例一致）
        ratio = dist / (a / px)
        ok_lo = ratio >= ATR_MIN_RATIO
        ok_hi = dist <= MAX_DISTANCE
        below = ma < px
        if ok_lo and ok_hi:
            # ⚠ 2026-09-12（2308 實測）：雙邊規則只管距離，不管方向 —— 但方向決定這個位階是哪一種。
            #   invalidation 是「失效價位」，必須在價格下方；價格上方的合格位階是 confirm_trigger 的候選。
            #   初版兩者都印「✓ 可用」，會讓人把一條壓力線寫進 invalidation。
            verd = "✓ 可作 invalidation" if below else "✓ 可作 confirm_trigger（在價格上方）"
        elif not ok_lo and not ok_hi:
            verd = "✗ 下界與上界都沒過"
        elif not ok_lo:
            verd = "✗ 未過 2 倍下界（與雜訊分不開）"
        else:
            verd = "✗ 超出 ±20% 上界（太遠，不構成有意義的位階）"
        print("MA%-4d %10.2f   %s %5.2f%%   %6.2f%%   %6.2f   %s"
              % (n, ma, "在價格上方" if ma > px else "在價格下方", abs(rel) * 100,
                 dist * 100, ratio, verd))
    print()
    v = valuation(tk, market)
    if v:
        print("官方倍數（%s）：%s" % (v.pop("日期"),
                                 "　".join("%s %s" % (k, x) for k, x in v.items())))
    print("⚠ 官方倍數是 trailing 口徑，不得用作 forward 基準年的錨（6531／3131 皆踩過）。")
    print()
    print("--- 最近 8 個交易日（用來對位第三方頁面的日期標籤）---")
    for r in b[-8:]:
        print("  %s  開 %9.2f  高 %9.2f  低 %9.2f  收 %9.2f" % r)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="+", help="台股代號，可多個")
    ap.add_argument("--months", type=int, default=4,
                    help="往回取幾個月的逐日資料（預設 4，足以算 MA60 與 ATR20；"
                         "要 MA120 用 8，要 MA240 用 14）")
    ap.add_argument("--refresh", action="store_true", help="忽略快取重抓")
    a = ap.parse_args()
    for tk in a.tickers:
        report(tk, a.months, a.refresh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
