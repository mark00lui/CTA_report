#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""跨清單重算 —— 把每一項聚合檢查對「全部」標的跑一次，而不是只對新做的那幾檔。

這支腳本存在的理由是一個實際犯過的錯（2026-09-12 的 24 檔作業）：

    「算術與幾何加權跨越零」我在第 18 輪（3211）稱首見、第 20 輪（2337）稱第二次 ——
    手算重排後說是三檔（最早的 3131 是第 8 輪），而這支腳本跑出來是**台股四檔、全清單六檔**：
    手算把權重硬寫成 0.25/0.50/0.25（24 檔裡 21 檔是那樣），漏掉 2308（0.30/0.50/0.20），
    而 2308 是整個作業的**第 1 輪**。⚠ 修正這個錯的那一次，又犯了同一個錯。
    「倍數段佔對數全距最高」我在第 21 輪（3030）稱 84.2% 為全系列最高、第 23 輪又重複一次 ——
    實際最高是 3008 的 85.1%（第 4 輪）。

兩次的根因相同：指標是中途才成為例行計算的，而我只把它對「引入之後處理的標的」算過，
然後拿那個子集合說「全系列最…」。序數描述因此只對子集合成立，
而讀者（包括下一輪的我）會把它讀成對全集合成立。

⚠ 「首見」是這份研究記錄用來標示方法層演進的主要標記。它失去意義的代價，
   遠大於某個數字差 0.1pp。所以這支腳本的輸出要在下任何序數結論之前看一次。

用法：
    python scripts/cross_check.py            # 全部標的
    python scripts/cross_check.py --tw       # 只看台股 24 檔
    python scripts/cross_check.py --quiet    # 只印硬錯與旗標，不印總表
    python scripts/cross_check.py --gate     # pre-commit 閘門：只印硬錯，旗標收成一行

硬錯（exit 1）—— 這些是算術不自洽，不是判斷問題：
    E1  三情境機率合計 ≠ 1.00
    E2  weighted_tp 欄位 ≠ 由三格算出來的值
    E3  某格的 tp ≠ eps × exit_multiple（eps 為數值時才檢）

⚠ E1 與 validate_state.py 的機率合計檢查重複（刻意保留：這支腳本要能獨立跑）。
  **E2 與 E3 在 2026-09-12 併入 .githooks/pre-commit 之前沒有任何機械檢查 ——
  那就是把它併進閘門的理由。** 旗標 F1–F7 不擋 commit，且在閘門模式下收成一行：
  27 檔的旗標每次 commit 都印一遍，會洗掉真正要看的那幾行。

旗標（exit 0，僅報告）—— 這些是要被看見的結構特徵，不是錯：
    F1  算術與幾何加權跨越零  → thesis 近乎二元，加權平均描述一個不會發生的中間狀態
    F2  全距 ≥ 5 倍            → 門檻自 3 倍提高而來（3 倍在 24 檔裡觸發 18 檔，不是篩子）
    F3  倍數段佔對數全距 ≥ 70% → 寬度集中在倍數，模型在賭重評價而非賭盈餘
    F8  倍數段佔對數全距 > 100% → 算術上不可能，故 exit_multiple 不是全公司倍數
        （E3／F6／F7 對該檔不適用）
    F4  base 落在現價 ±5% 內   → 可能是結論，也可能是沒有獨立意見的產物，報告必須分清
    F5  |加權 − base| ≤ 2pp    → 兩翼對頭條幾乎沒有貢獻（只貢獻寬度，而頭條不報寬度）
    F6  三情境分母完全相同      → 不是三情境，是對同一個盈餘的三種市場願付價格
    F7  反推分母非單調遞增      → eps 為 __ 時 E3 查不到，改由 tp ÷ 倍數反推並檢查方向
"""
import io, os, sys, glob, math, argparse

# 與 validate_state.py / check_public.py 同樣的理由，而這支腳本是在 pre-commit hook 裡
# 實測發現的：hook 的環境沒有 PYTHONIOENCODING，Windows 主控台用 cp950，
# 於是硬錯訊息印成亂碼。看不懂的錯誤訊息等於半個閘門。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:
    print("需要 pyyaml：pip install pyyaml"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW = ['2308', '8046', '3037', '3008', '6531', '3081', '8299', '3131',
      '6239', '6805', '2345', '3661', '3017', '3583', '3533', '3665',
      '2317', '3211', '6187', '2337', '3030', '3324', '6442', '3363']
CELLS = ('bear', 'base', 'bull')


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def load(path):
    with io.open(path, encoding='utf-8') as fh:
        return yaml.safe_load(fh.read())


def geo(tp, p):
    """機率加權的幾何平均。tp 必須全為正。"""
    if any(v is None or v <= 0 for v in tp):
        return None
    return math.exp(sum(p[i] * math.log(tp[i]) for i in range(3)))


def analyse(tk, d):
    """回傳 (row, errors, flags)。row 的值可能為 None —— 資料不足就留白，不猜。"""
    errs, flags = [], []
    sc = (d or {}).get('scenarios')
    if not isinstance(sc, dict):
        return None, [], []
    cells = [sc.get(c) or {} for c in CELLS]
    p = [num(c.get('p')) for c in cells]
    tp = [num(c.get('tp')) for c in cells]
    eps = [num(c.get('eps')) for c in cells]
    mul = [num(c.get('exit_multiple')) for c in cells]
    px = num((d.get('cta') or {}).get('price'))
    wf = num(sc.get('weighted_tp'))

    # ---- 硬錯 ----
    if all(v is not None for v in p):
        if abs(sum(p) - 1.0) > 1e-6:
            errs.append('E1 機率合計 %.4f ≠ 1.00' % sum(p))
    if all(v is not None for v in p + tp) and wf is not None:
        calc = sum(p[i] * tp[i] for i in range(3))
        # 容忍四捨五入到整數
        if abs(calc - wf) > max(1.0, abs(calc) * 0.002):
            errs.append('E2 weighted_tp %s ≠ 由三格算出的 %.1f' % (wf, calc))
    for i, c in enumerate(CELLS):
        if eps[i] is not None and mul[i] is not None and tp[i] is not None:
            calc = eps[i] * mul[i]
            if abs(calc - tp[i]) > max(1.0, abs(calc) * 0.005):
                errs.append('E3 %s: %s × %s = %.1f ≠ tp %s' % (c, eps[i], mul[i], calc, tp[i]))

    # ---- 聚合量 ----
    row = {'tk': tk, 'px': px, 'w': wf}
    # ⚠⚠⚠ 2026-09-12：把 ATR20 占收盤比納入排名。
    #   理由是一個實際犯過的錯：TSM 那一輪我宣稱「ATR 2.377% 是台股 24 檔與美股 15 檔合計裡最低」，
    #   而當時只有 27/39 檔算過 ATR —— MSFT 的 1.953% 在一檔之內就推翻它。
    #   CLAUDE.md 已記著同類錯誤犯過三次，而那條紀律說「下序數結論前先跑 cross_check」——
    #   但 ATR 不在 cross_check 的輸出裡，所以那條紀律對 ATR 型結論完全沒有覆蓋。
    #   ⚠ 排名區塊會印出「已算出 N 檔」，因為分母本身就是那個錯誤的來源。
    atr = (d.get('cta') or {}).get('atr20')
    if atr and px:
        try:
            row['atr_ratio'] = float(atr) / float(px)
        except (TypeError, ValueError):
            pass
    # ⚠ 2026-09-12 實測：我上一輪的跨清單重算把權重硬寫成 0.25/0.50/0.25（24 檔裡 21 檔是那樣），
    #   結果 2308（實際 0.30/0.50/0.20）的幾何加權算成 +1.1% 而非 -3.6% —— 漏掉一個跨越零的實例，
    #   而它是整個作業的第 1 輪。機率是使用者指定的，不得假設。把它印出來，讓偏離無法安靜通過。
    if all(v is not None for v in p) and p != [0.25, 0.5, 0.25]:
        row['pnote'] = '⚠ p=%s' % '/'.join('%g' % v for v in p)
    if wf is not None and px:
        row['arith'] = wf / px - 1.0
    g = geo(tp, p) if all(v is not None for v in p) else None
    if g is not None and px:
        row['geom'] = g / px - 1.0
    if all(v is not None and v > 0 for v in tp):
        row['spread'] = tp[2] / tp[0]
    if eps[0] and eps[2]:
        row['eps_seg'] = eps[2] / eps[0]
    if mul[0] and mul[2]:
        row['mul_seg'] = mul[2] / mul[0]
    if row.get('spread', 0) > 1 and row.get('mul_seg', 0) > 1:
        row['mul_share'] = math.log(row['mul_seg']) / math.log(row['spread'])
    if tp[1] is not None and px:
        row['base_up'] = tp[1] / px - 1.0

    # ---- 旗標 ----
    a, gg = row.get('arith'), row.get('geom')
    if a is not None and gg is not None and a * gg < 0:
        flags.append('F1 算術 %+.1f%% 與幾何 %+.1f%% 跨越零 → 方向性判斷不穩健' % (a * 100, gg * 100))
    if row.get('spread') and row['spread'] >= 5.0:
        flags.append('F2 全距 %.2f 倍 ≥ 5' % row['spread'])
    if row.get('mul_share') and row['mul_share'] >= 0.70:
        flags.append('F3 倍數段佔對數全距 %.0f%% ≥ 70%%' % (row['mul_share'] * 100))
    # F8：倍數段佔比 > 100% —— 這在「tp ＝ 共同 eps × 倍數」的分解下是算術上不可能的，
    #     因為兩段相加恰等於全距。所以它證明 exit_multiple 不是全公司的倍數。
    #     2026-09-12（INTC）實測 149%：該檔的目標價是三個分部加總，而 exit_multiple
    #     只記了 Intel Foundry 一個分部的市值／PPE。當時 F7 照樣誤報了，
    #     而 F3 的 149% 本來就能攔下它 —— 只是它被當成一個「偏向倍數」的旗標而非偵測器。
    #     ⚠ 本條只報告，不自動抑制 E3／F6／F7：抑制會改變其他檔的行為，
    #       需要逐檔確認哪些是反算型的倍數，屬覆蓋層工作。
    if row.get('mul_share') and row['mul_share'] > 1.0:
        flags.append(
            'F8 倍數段佔對數全距 %.0f%% > 100%% —— 在「tp ＝ 共同 eps × 倍數」下算術上不可能，'
            '故此檔的 exit_multiple 不是全公司倍數；E3／F6／F7 對它不適用，讀 multiple_basis'
            % (row['mul_share'] * 100))
    if row.get('base_up') is not None and abs(row['base_up']) <= 0.05:
        flags.append('F4 base 落在現價 %+.1f%%（±5%% 內）→ 報告須分清是結論還是沒有獨立意見' % (row['base_up'] * 100))
    if a is not None and row.get('base_up') is not None and abs(a - row['base_up']) <= 0.02:
        flags.append('F5 加權與 base 只差 %+.1f pp → 兩翼對頭條幾乎沒有貢獻' % ((a - row['base_up']) * 100))

    # F6：三格分母相同 —— 全部寬度都在倍數上。INTU 實例：eps 三格都是 23.00，
    #     倍數 9.6／20.2／23.8。那不是對事業的三種判斷，是對同一個盈餘的三種願付價格。
    if all(v is not None for v in eps) and eps[0] == eps[1] == eps[2]:
        flags.append('F6 三情境 eps 全為 %s → 寬度 100%% 來自倍數，情境未對事業做任何區分' % eps[0])

    # F7：eps 為 __ 時 E3 無從檢查，但分母可由 tp ÷ 倍數反推。
    #     INTC 實例：PB 0.5／1.2／2.2 配 tp 43／73／116，反推每股淨值 86／60.8／52.7 ——
    #     情境愈好分母愈低。那可能是「縮編到獲利核心」的真實結構，但必須被明寫而不是被默認。
    if any(v is None for v in eps) and all(v for v in mul) and all(v is not None for v in tp):
        den = [tp[i] / mul[i] for i in range(3)]
        if not (den[0] <= den[1] <= den[2]):
            flags.append('F7 反推分母 %.1f／%.1f／%.1f 非單調遞增（倍數 %s／%s／%s）'
                         ' → 分母隨情境變動的理由必須在 multiple_basis 明寫'
                         % (den[0], den[1], den[2], mul[0], mul[1], mul[2]))
    return row, errs, flags


def rank(rows, key, label, reverse=True, fmt='%.2f', mul=1.0):
    """把序數結論印出來，讓「首見／最高／最低」可以被核對而不是被記憶。"""
    have = [r for r in rows if r.get(key) is not None]
    if not have:
        return
    have.sort(key=lambda r: r[key], reverse=reverse)
    top = have[:3]
    bot = have[-3:][::-1]
    print('  %-22s 最高 %s   最低 %s' % (
        label,
        ' / '.join('%s %s' % (r['tk'], fmt % (r[key] * mul)) for r in top),
        ' / '.join('%s %s' % (r['tk'], fmt % (r[key] * mul)) for r in bot)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tw', action='store_true', help='只看台股 24 檔')
    ap.add_argument('--quiet', action='store_true', help='不印總表')
    ap.add_argument('--gate', action='store_true',
                    help='pre-commit 閘門：只印硬錯，旗標收成一行')
    a = ap.parse_args()
    if a.gate:
        a.quiet = True

    paths = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'state', '*.yaml'))):
        b = os.path.basename(f)
        if b.startswith('_') or b == 'coverage.yaml':
            continue
        tk = b[:-5]
        if a.tw and tk not in TW:
            continue
        paths.append((tk, f))

    rows, all_err, all_flag = [], [], []
    for tk, f in paths:
        try:
            d = load(f)
        except Exception as e:
            all_err.append((tk, ['讀取失敗：%s' % e])); continue
        row, errs, flags = analyse(tk, d)
        if row:
            rows.append(row)
        if errs:
            all_err.append((tk, errs))
        if flags:
            all_flag.append((tk, flags))

    if not a.quiet:
        print('=== 跨清單重算（%d 檔）===' % len(rows))
        print('%-6s %9s %9s %8s %8s %7s %7s %7s %8s  %s' % (
            'tk', 'price', 'wtp', 'arith', 'geom', 'spread', 'epsSeg', 'mulSeg', 'mulShare', '非標準機率'))
        for r in sorted(rows, key=lambda r: -(r.get('mul_share') or 0)):
            def g(k, f, d='     -', mul=1.0):
                return (f % (r[k] * mul)) if r.get(k) is not None else d
            print('%-6s %9s %9s %8s %8s %7s %7s %7s %8s  %s' % (
                r['tk'], g('px', '%9.2f'), g('w', '%9.0f'),
                g('arith', '%+7.1f%%', mul=100), g('geom', '%+7.1f%%', mul=100),
                g('spread', '%6.2fx'), g('eps_seg', '%6.2fx'),
                g('mul_seg', '%6.2fx'), g('mul_share', '%7.0f%%', mul=100),
                r.get('pnote', '')))
        print()
        print('--- 序數結論（下「首見／最高／最低」之前看這裡）---')
        rank(rows, 'atr_ratio', 'ATR20 占收盤比', fmt='%.3f%%', mul=100)
        _na = [r['tk'] for r in rows if r.get('atr_ratio') is None]
        if _na:
            print('  %-22s 已算出 %d 檔；未算 %d 檔：%s'
                  % ('　（ATR 的分母）', len(rows) - len(_na), len(_na), ' '.join(sorted(_na))))
        rank(rows, 'spread', '全距', fmt='%.2fx')
        rank(rows, 'mul_share', '倍數段佔對數全距', fmt='%.0f%%', mul=100)
        rank(rows, 'arith', '算術加權上檔', fmt='%+.0f%%', mul=100)
        rank(rows, 'geom', '幾何加權上檔', fmt='%+.0f%%', mul=100)
        x = [r for r in rows if r.get('arith') is not None and r.get('geom') is not None and r['arith'] * r['geom'] < 0]
        print('  %-22s %s' % ('跨越零', ' / '.join(r['tk'] for r in x) if x else '無'))
        n = lambda k, c: sum(1 for r in rows if r.get(k) is not None and c(r[k]))
        print('  %-22s 算術為負 %d／%d；幾何為負 %d／%d；全距 ≥3x %d；≥5x %d' % (
            '計數', n('arith', lambda v: v < 0), len(rows), n('geom', lambda v: v < 0), len(rows),
            n('spread', lambda v: v >= 3), n('spread', lambda v: v >= 5)))
        print()

    if all_flag and not a.gate:
        print('--- 旗標（僅報告，不擋 commit）---')
        for tk, fl in all_flag:
            for s in fl:
                print('  [%s] %s' % (tk, s))
        print()

    if all_err:
        print('=== 硬錯 ===')
        for tk, es in all_err:
            for s in es:
                print('  [%s] %s' % (tk, s))
        print('\n有 %d 檔算術不自洽。' % len(all_err))
        return 1
    if a.gate:
        print('  ✓ %d 檔三情境算術自洽（E1–E3）；%d 檔帶旗標 —— '
              '細節跑 python scripts/cross_check.py'
              % (len(rows), len(all_flag)))
    else:
        print('✓ 算術自洽：%d 檔無硬錯（%d 檔帶旗標）' % (len(rows), len(all_flag)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
