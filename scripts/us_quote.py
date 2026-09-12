# -*- coding: utf-8 -*-
"""美股版的 official_quote.py —— 收盤 + ATR20 + 六條均線 + 區間 + 雙邊規則判定。

用法：
    python scripts/us_quote.py INTU
    python scripts/us_quote.py INTU --years 2

⚠⚠⚠ **與台股版最重要的差別：美股沒有免費的官方價格通道。**
SEC 不發布價格（`data.sec.gov` 只有 XBRL 財報），交易所的逐筆／日線要付費。
所以本腳本走 Yahoo Finance 的 chart JSON 端點，**那是「最佳可得」而不是「官方」**
—— 台股版可以說「證交所官方逐日」，本腳本不可以。

**必須做的交叉驗證**：把最後一根收盤與 stockanalysis.com/stocks/<ticker>/ 的報價對照。
2026-09-12 首次使用時，INTU 的 2026-09-10 收盤 312.77 與 state 既記的 stockanalysis 值
完全相符 —— 那是這個通道可信的第一個證據，但每檔都要再對一次。

⚠ 其他坑：
  * 端點需要 User-Agent，否則回 429／403。
  * 回傳含當日盤中未收盤的那一根；本腳本不過濾，**請自己看最後一根的日期**
    （美股收盤後才會定案，而台北時間的「今天」通常是美股的「昨天」）。
  * `null` 會出現在 OHLC 裡（半日市、資料缺漏），本腳本跳過並報出 —— 與台股版的零成交日同一處理。
  * 均線同時算兩組：**本倉庫的 5/10/20/60/120/240**（使雙邊規則與台股可比）
    與**美股慣用的 50/200 DMA**（state 既有欄位用的是這一組）。
"""
import io
import json
import os
import subprocess
import sys
import datetime

ATR_MIN_RATIO = 2.0      # 下界：距離須達 2 倍 ATR20（擋「與雜訊分不開」）
MAX_DISTANCE = 0.20      # 上界：距離不得超過現價的 20%（擋「太遠所以永遠不會發生」）
WEEK_FACTOR = 5 ** 0.5   # 週的真實區間約為日 ATR 的 √5，時間濾網用

CACHE = os.path.join(os.environ.get('TEMP', '/tmp'), 'cta_us_quote')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
SKIPPED = []


def fetch(tk, years):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, '%s_%dy.json' % (tk.upper(), years))
    if not os.path.exists(p) or os.path.getsize(p) < 500:
        url = ('https://query1.finance.yahoo.com/v8/finance/chart/%s'
               '?range=%dy&interval=1d' % (tk.upper(), years))
        subprocess.run(['curl', '-s', '--max-time', '60', '-A', UA, url, '-o', p], check=True)
    return json.load(io.open(p, encoding='utf-8'))


def bars(tk, years):
    """回傳 [(iso_date, open, high, low, close)]，依日期遞增。"""
    d = fetch(tk, years)
    r = d['chart']['result'][0]
    meta = r['meta']
    ts = r['timestamp']
    q = r['indicators']['quote'][0]
    out = []
    for i, t in enumerate(ts):
        o, h, l, c = q['open'][i], q['high'][i], q['low'][i], q['close'][i]
        d0 = datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime('%Y-%m-%d')
        if None in (o, h, l, c):
            SKIPPED.append(d0)
            continue
        out.append((d0, o, h, l, c))
    out.sort(key=lambda x: x[0])
    return out, meta


def atr(bs, n=20):
    trs = []
    for i in range(1, len(bs)):
        pc = bs[i - 1][4]
        h, l = bs[i][2], bs[i][3]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-n:]) / n


def ma(bs, n):
    return sum(b[4] for b in bs[-n:]) / n


def verdict(v, px, a):
    d = abs(v - px)
    dd = d / px * 100
    r = d / a
    below = v < px
    wk = r * WEEK_FACTOR
    if dd > MAX_DISTANCE * 100:
        return '✗ 超出 ±20%% 上界（超界 %.2fpp）' % (dd - MAX_DISTANCE * 100)
    if r >= ATR_MIN_RATIO:
        return '✓ 可作 invalidation' if below else '✓ 可作 confirm_trigger（在價格上方）'
    if wk >= ATR_MIN_RATIO:
        return ('✓ 經週收盤濾網（%.2f）可作 invalidation' % wk if below
                else '⚠ 週收盤濾網下為 %.2f —— 但濾網對上方位階是否成立尚未裁決' % wk)
    return '✗ 未過 2 倍下界（週收盤等效僅 %.2f）' % wk


def main():
    tk = sys.argv[1].upper()
    years = 2
    if '--years' in sys.argv:
        years = int(sys.argv[sys.argv.index('--years') + 1])
    b, meta = bars(tk, years)
    px = b[-1][4]
    a = atr(b)
    print('=' * 72)
    print('%s（%s，%s）  收盤 %.2f  日期 %s  共 %d 根（%s ~ %s）'
          % (tk, meta.get('fullExchangeName', '?'), meta.get('currency', '?'),
             px, b[-1][0], len(b), b[0][0], b[-1][0]))
    print('=' * 72)
    print('⚠⚠ 來源是 Yahoo chart 端點 —— 最佳可得，不是官方。'
          '請與 stockanalysis.com/stocks/%s/ 對照最後一根收盤。' % tk.lower())
    if SKIPPED:
        print('⚠ 有 %d 天的 OHLC 含 null 而被跳過：%s' % (len(SKIPPED), '／'.join(SKIPPED)))
    print()
    print('當日 開 %.2f  高 %.2f  低 %.2f  收 %.2f' % b[-1][1:])
    print('ATR20 %.2f ＝ 收盤的 %.3f%%' % (a, a / px * 100))
    amp = (b[-1][2] - b[-1][3]) / px * 100
    print('當日振幅 %.2f%%（＝ ATR 的 %.2f 倍）⚠ 單日振幅不得當門檻分母，偏誤方向不固定'
          % (amp, amp / (a / px * 100)))
    print()
    hi = max(x[2] for x in b)
    lo = min(x[3] for x in b)
    hid = [x[0] for x in b if x[2] == hi][0]
    lod = [x[0] for x in b if x[3] == lo][0]
    print('全窗口高 %.2f（%s）  低 %.2f（%s）  高低比 %.2f 倍' % (hi, hid, lo, lod, hi / lo))
    cut = (datetime.date.fromisoformat(b[-1][0]) - datetime.timedelta(days=365)).isoformat()
    w = [x for x in b if x[0] >= cut]
    whi = max(x[2] for x in w)
    wlo = min(x[3] for x in w)
    whid = [x[0] for x in w if x[2] == whi][0]
    wlod = [x[0] for x in w if x[3] == wlo][0]
    print('真 52 週（自 %s，%d 根）高 %.2f（%s）低 %.2f（%s）高低比 %.2f 倍'
          % (cut, len(w), whi, whid, wlo, wlod, whi / wlo))
    print('  現價距 52 週高 %+.2f%%；52 週低距現價 %.2f%% ＝ %.2f 倍 ATR  %s'
          % ((px / whi - 1) * 100, (px - wlo) / px * 100, (px - wlo) / a,
             verdict(wlo, px, a)))
    print()
    print('%-7s %10s %10s %9s %8s %8s  %s'
          % ('均線', '值', '價格相對', '距現價', '倍 ATR', '週等效', '判定'))
    for n in (5, 10, 20, 50, 60, 100, 120, 200, 240):
        if len(b) < n:
            print('MA%-5d  （資料不足 %d 根）' % (n, n))
            continue
        v = ma(b, n)
        d = abs(v - px)
        tag = '  ← 美股慣用' if n in (50, 200) else ''
        print('MA%-5d %10.2f %10s %8.2f%% %8.2f %8.2f  %s%s'
              % (n, v, '下方' if v < px else '上方', d / px * 100, d / a,
                 d / a * WEEK_FACTOR, verdict(v, px, a), tag))
    print()
    print('--- 最近 8 個交易日（用來對位第三方頁面的日期標籤）---')
    for x in b[-8:]:
        print('  %s  開 %9.2f 高 %9.2f 低 %9.2f 收 %9.2f' % x)


if __name__ == '__main__':
    main()
