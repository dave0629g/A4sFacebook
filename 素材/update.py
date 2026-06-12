#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""素材更新引擎 ── 小編提供資料後，跑這支就立即更新所有成果。

用法（在專案根目錄）：
    python3 素材/update.py

它會：
  ① 讀 素材/提供資料.yaml（第一次自動從 .範例 複製一份）
  ② 把已拿到的值代入文案模板（執行包 02/03/05）→ 寫出可直接複製的成品到 素材/成品/
  ③ 把 素材/收件匣/ 的檔案依檔名歸位到 素材/實品/，清點本機原圖資料夾
  ④ 算出每項素材的狀態與「下一個死線」→ 寫 素材/狀態.md，並在終端機印出摘要

沒拿到的值會在成品裡保留【佔位】，不會憑空捏造。
個資（真實姓名/電話/稅務）不經過這支程式，只存共用資料夾。
"""
import os
import re
import shutil
import datetime
import sys

try:
    import yaml
except ImportError:
    sys.exit('需要 pyyaml：請執行  pip3 install pyyaml')

ROOT = os.path.dirname(os.path.abspath(__file__))            # 素材/
REPO = os.path.dirname(ROOT)
EXEC = os.path.join(REPO, '執行包')
DATA = os.path.join(ROOT, '提供資料.yaml')
SAMPLE = os.path.join(ROOT, '提供資料.範例.yaml')
INBOX = os.path.join(ROOT, '收件匣')
ACTUAL = os.path.join(ROOT, '實品')
OUT = os.path.join(ROOT, '成品')
STATUS = os.path.join(ROOT, '狀態.md')
PHOTO_ROOT = os.path.expanduser('~/A4s音樂會素材原圖')

TODAY = datetime.date.today()
YEAR = 2026
IMG_EXT = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif'}

# ── 得獎名單在模板裡的遮蔽佔位（照抽出順序對應正取 1–5、備取 1–2）──
WINNER_TOKENS = ['王Ｏ明', '李Ｏ華', '陳Ｏ安', '黃Ｏ珊', '吳Ｏ哲']
BACKUP_TOKENS = ['林Ｏ婷', '張Ｏ豪']


def load_data():
    if not os.path.exists(DATA):
        shutil.copy(SAMPLE, DATA)
        print(f'（第一次執行：已建立 {os.path.relpath(DATA, REPO)}，請打開來填，再跑一次）')
    with open(DATA, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def g(d, path, default=''):
    """以 'a.b.c' 取巢狀值；空字串/None 視為未填。"""
    cur = d
    for k in path.split('.'):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur if cur is not None else default


def filled(v):
    if v is True:
        return True
    if v in (False, None):
        return v is True
    return bool(str(v).strip())


# ════════════════════════════════════════════════════════════════
#  ② 代入文案 → 成品
# ════════════════════════════════════════════════════════════════
def build_replacements(d):
    L = d.get('連結', {}) or {}
    R = d.get('票選結果', {}) or {}
    W = d.get('得獎名單', {}) or {}
    feels = d.get('聽後感', []) or []

    s1 = str(g(R, '第一名曲名'))
    s2 = str(g(R, '第二名曲名'))
    s3 = str(g(R, '第三名曲名'))
    pax = str(g(R, '參加人數'))
    正取 = list(W.get('正取') or [])
    備取 = list(W.get('備取') or [])

    pairs = []  # (find, replacement) — 只有值有填才加入，沒填就留原本的【佔位】

    def add(find, val, repl=None):
        if filled(val):
            pairs.append((find, repl if repl is not None else str(val)))

    # 連結類
    add('【短網址】', g(L, '短網址A'))
    add('【短網址B】', g(L, '短網址B'))
    add('【辦法短網址】', g(L, '辦法短網址'))
    add('【開獎貼文連結】', g(L, '開獎貼文連結'))
    # 曲名（依前後文精準替換，避免三個【曲名】混在一起）
    add('第一名：【曲名】', s1, f'第一名：{s1}')
    add('第二名：【曲名】', s2, f'第二名：{s2}')
    add('第三名：【曲名】', s3, f'第三名：{s3}')
    add('第一名的【曲名】', s1, f'第一名的{s1}')
    add('【冠軍曲名】', s1)
    # 參加人數
    add('【參加人數】', pax)
    # 得獎名單（遮蔽版）。正取各自一行，逐一替換
    for tok, val in zip(WINNER_TOKENS, 正取 + [''] * 5):
        add(f'【{tok}】', val)
    # 備取兩人在模板同一行（原本靠【】分隔），合併替換並補頓號避免黏在一起
    b1 = 備取[0] if len(備取) > 0 else ''
    b2 = 備取[1] if len(備取) > 1 else ''
    backup_pair = f'【{BACKUP_TOKENS[0]}】【{BACKUP_TOKENS[1]}】'
    if filled(b1) and filled(b2):
        pairs.append((backup_pair, f'{b1}、{b2}'))
    elif filled(b1):                       # 只填 1 位備取也整組換掉，不留殘缺佔位
        pairs.append((backup_pair, b1))
    elif filled(b2):
        pairs.append((backup_pair, b2))
    # 聽後感（引用＋暱稱整組替換；composite token 唯一，只會換一次）
    for i in range(3):
        q = g(feels[i], '引用') if i < len(feels) else ''
        n = g(feels[i], '暱稱') if i < len(feels) else ''
        if filled(q):
            nick = n if filled(n) else '【暱稱】'
            pairs.append((f'【聽後感引用 {i + 1}】」——【暱稱】', f'{q}」——{nick}'))
    return pairs


def render(d):
    os.makedirs(OUT, exist_ok=True)
    pairs = build_replacements(d)
    templates = [
        ('02_團員私訊模板.md', '成品_團員私訊.md'),
        ('03_粉專貼文文案.md', '成品_粉專貼文.md'),
        ('05_LINE訊息版.md', '成品_LINE訊息.md'),
    ]
    rendered = []
    for src, dst in templates:
        sp = os.path.join(EXEC, src)
        if not os.path.exists(sp):
            continue
        text = open(sp, encoding='utf-8').read()
        for find, repl in pairs:
            text = text.replace(find, repl)
        remaining = len(re.findall(r'【[^】]*】', text))
        banner = (f'<!-- 此檔由 update.py 自動產生，請勿手動編輯；改值請改 提供資料.yaml 後重跑。 -->\n'
                  f'<!-- 產生時間：{TODAY.isoformat()}　尚有 {remaining} 個【佔位】待填 -->\n'
                  f'<!-- 註：私訊模板的【暱稱】【當天小事】是團員自己填的，屬正常保留 -->\n\n')
        open(os.path.join(OUT, dst), 'w', encoding='utf-8').write(banner + text)
        rendered.append((dst, remaining))
    return rendered


# ════════════════════════════════════════════════════════════════
#  ③ 收件匣歸位 + 清點本機原圖
# ════════════════════════════════════════════════════════════════
ROUTE = [  # (關鍵字, 實品子資料夾)
    (('洞察', '追蹤', 'insight', 'kpi'), '01_KPI基準'),
    (('演出', '謝幕', '第一波'), '03_第一波照片'),
    (('彩排', '幕後', '觀眾', '花絮', '第二波'), '04_第二波照片'),
    (('轉盤', '抽獎', '正取', '備取', 'wheel'), '06_抽獎存證'),
    (('圖卡', '揭曉', '前三名'), '07_開獎素材'),
    (('合影', '領獎', '同意'), '08_領獎與結案'),
    (('票面', '入場券', '發票', 'usb', '市價'), '09_獎品與合規存證'),
]


def route_inbox():
    moved = []
    if not os.path.isdir(INBOX):
        os.makedirs(INBOX, exist_ok=True)
        return moved
    for name in os.listdir(INBOX):
        if name.startswith('.'):
            continue
        src = os.path.join(INBOX, name)
        if not os.path.isfile(src):
            continue
        low = name.lower()
        sub = '未分類'
        for keys, folder in ROUTE:
            if any(k.lower() in low for k in keys):
                sub = folder
                break
        dstdir = os.path.join(ACTUAL, sub)
        os.makedirs(dstdir, exist_ok=True)
        shutil.move(src, os.path.join(dstdir, name))
        moved.append((name, sub))
    return moved


def count_images(folder):
    if not os.path.isdir(folder):
        return 0
    return sum(1 for n in os.listdir(folder)
               if os.path.splitext(n)[1].lower() in IMG_EXT and not n.startswith('.'))


def count_files(folder):
    """計任意檔案（含 PDF 收據、發票等非影像證明），排除隱藏檔。"""
    if not os.path.isdir(folder):
        return 0
    return sum(1 for n in os.listdir(folder)
               if not n.startswith('.') and os.path.isfile(os.path.join(folder, n)))


def actual_images(sub):
    return count_images(os.path.join(ACTUAL, sub))


# ════════════════════════════════════════════════════════════════
#  ④ 狀態判定
# ════════════════════════════════════════════════════════════════
# 每項：(死線(月,日), 批次, 名稱, 判定函式 → bool, 備註)
def build_manifest(d):
    def val(path):
        return lambda: filled(g(d, path))

    def flag(path):
        return lambda: g(d, path, False) is True

    def photos(sub, ext_subdir, n=1):
        return lambda: (actual_images(sub) + count_images(os.path.join(PHOTO_ROOT, ext_subdir))) >= n

    def files(sub, n=1):
        # 計任意檔案：證明類常是 PDF，截圖/圖卡是影像，一律算「檔案到了沒」
        return lambda: count_files(os.path.join(ACTUAL, sub)) >= n

    M = [
        ((6, 12), '6/12 今晚', '追蹤者 6/12 精確基準', val('KPI.追蹤者_0612基準'), '今晚不記就補不回'),
        ((6, 12), '6/12 今晚', 'Meta 洞察 30 天淨增截圖', files('01_KPI基準'), '丟收件匣或共用資料夾'),
        ((6, 12), '6/12 今晚', '共用資料夾連結', val('連結.共用資料夾'), ''),
        ((6, 12), '6/12 今晚', '認領名單試算表', val('連結.認領名單試算表'), '加首發/提醒兩欄'),
        ((6, 12), '6/12 今晚', '辦法文件＋短網址', flag('完成.辦法文件已建並設好權限'), ''),
        ((6, 12), '6/12 今晚', '辦法短網址（值）', val('連結.辦法短網址'), ''),
        ((6, 12), '6/12 今晚', '管理試算表連結', val('連結.管理試算表'), '只給幹部，不給全團'),
        ((6, 12), '6/12 今晚', '表單回覆者連結＋自動關閉已設', flag('完成.表單已建_自動關閉已設'), ''),
        ((6, 12), '6/12 今晚', '短網址 A／B 已縮', lambda: filled(g(d, '連結.短網址A')) and filled(g(d, '連結.短網址B')), 'reurl 同帳號'),
        ((6, 12), '6/12 今晚', '手機實測表單 OK（用短網址A）', flag('完成.手機實測_表單OK'), ''),
        ((6, 12), '6/12 今晚', '粉專追蹤者名單可開', flag('完成.手機實測_粉專追蹤者名單可開'), '領獎查核備用'),

        ((6, 13), '6/13 開跑前', 'reurl 帳密已記幹部文件', flag('完成.reurl帳密已記幹部文件'), ''),
        ((6, 13), '6/13 開跑前', '入場券票面價證明', files('09_獎品與合規存證'), ''),
        ((6, 13), '6/13 開跑前', 'USB 市價／發票證明', flag('完成.獎品價值證明_皆未超過1000'), '兩種皆≤1000'),
        ((6, 13), '6/13 開跑前', '獎品實物各備 5 份', flag('完成.獎品實物_各備5份'), ''),
        ((6, 13), '6/13 開跑前', '計分方式已定案', flag('完成.計分方式已定案'), '開票後不得改'),
        ((6, 13), '6/13 開跑前', '指揮同意安可候選用語', flag('完成.指揮同意安可候選用語'), ''),
        ((6, 13), '6/13 開跑前', '幹部備援權限對方已接受', flag('完成.幹部備援權限_對方已接受'), ''),
        ((6, 13), '6/13 開跑前', 'gmail 有人每日收信', flag('完成.gmail有人每日收信'), ''),
        ((6, 13), '6/13 開跑前', '訊息 0/1/2 已依序貼群組', flag('完成.訊息012已依序貼團員群組'), '含開場公告訊息0'),

        ((6, 15), '6/14–15 第一波', '第一波照片已審片', flag('完成.第一波照片已審片'), '6/14 送審24h'),
        ((6, 15), '6/14–15 第一波', '第一波照片（原圖）', photos('03_第一波照片', '第一波_演出謝幕', 1), 'LINE相簿存本機原圖夾'),
        ((6, 15), '6/14–15 第一波', '第一波相簿＋貼文1連結', lambda: filled(g(d, '連結.第一波相簿')) and filled(g(d, '連結.貼文1')), ''),

        ((6, 18), '6/18 戰報', '各團員已填名單已個別私訊', flag('完成.各團員已填名單已個別私訊_0618'), ''),

        ((6, 20), '6/20–21 第二波', '第二波照片已審片', flag('完成.第二波照片已審片'), '6/20 送審留24h'),
        ((6, 21), '6/20–21 第二波', '第二波照片（原圖）', photos('04_第二波照片', '第二波_彩排幕後觀眾席', 1), ''),
        ((6, 21), '6/20–21 第二波', '第二波相簿＋貼文2.5連結', lambda: filled(g(d, '連結.第二波相簿')) and filled(g(d, '連結.貼文2_5')), ''),

        ((6, 26), '6/26 抽獎', '排除名單已填', flag('完成.排除名單已填'), '先填再按④'),
        ((6, 26), '6/26 抽獎', '人工判定已補登', flag('完成.人工判定已補登'), '之後別再按④'),
        ((6, 26), '6/26 抽獎', '轉盤名單已產生（按⑤）', flag('完成.轉盤名單已產生_按5'), '補登後才按⑤'),
        ((6, 26), '6/26 抽獎', '抽獎已錄影', flag('完成.抽獎已錄影'), '僅存證不公開'),
        ((6, 26), '6/26 抽獎', '轉盤截圖 7 張', files('06_抽獎存證', 7), '正取5+備取2'),
        ((6, 26), '6/26 抽獎', '參加人數（修正後）', val('票選結果.參加人數'), '人數不是票數'),
        ((6, 26), '6/26 抽獎', '前三名曲名', lambda: all(filled(g(d, f'票選結果.{k}')) for k in ('第一名曲名', '第二名曲名', '第三名曲名')), ''),
        ((6, 26), '6/26 抽獎', '得獎名單遮蔽版（正取5）', lambda: len([x for x in (d.get('得獎名單', {}) or {}).get('正取', []) or [] if filled(x)]) >= 5, ''),
        ((6, 26), '6/26 抽獎', '前三名揭曉圖卡', files('07_開獎素材'), ''),

        ((6, 27), '6/27–30 領獎', '開獎貼文連結', val('連結.開獎貼文連結'), ''),
        ((6, 28), '6/27–30 領獎', '未領獎名單已個別私訊', flag('完成.未領獎名單已個別私訊_0628'), ''),
        ((6, 30), '6/27–30 領獎', '稅務資料已抄存共用資料夾', flag('完成.稅務資料已抄存共用資料夾'), '若獎品逾千；按⑥前'),

        ((7, 1), '7/1 結案', '聽後感 3 則（可刊登）', lambda: len([f for f in (d.get('聽後感') or []) if filled(g(f, '引用'))]) >= 3, ''),
        ((7, 1), '7/1 結案', '7/1 追蹤數＋覆盤數字', lambda: all(filled(g(d, f'KPI.{k}')) for k in ('追蹤者_0701', '私訊發送數', '表單完成數')), ''),
        ((7, 1), '7/1 結案', '各團員歸因分布已抄存', flag('KPI.各團員歸因分布_已抄存'), '按⑥前，否則消失'),
        ((7, 1), '7/1 結案', '「我的最愛」操作已實測', flag('完成.我的最愛操作已實測'), ''),
        ((7, 1), '7/1 結案', '程式⑥已執行＋乾淨副本', flag('完成.程式6已執行_個資已清_副本已留'), ''),
    ]
    return M


def status_icon(done, deadline):
    dl = datetime.date(YEAR, *deadline)
    if done:
        return '✅'
    if dl < TODAY:
        return '⚠️'   # 逾期未完成
    if dl == TODAY:
        return '⏰'   # 今天到期
    return '☐'


def write_status(d, rendered, moved):
    M = build_manifest(d)
    rows = []
    done_n = 0
    for deadline, batch, name, check, note in M:
        try:
            done = bool(check())
        except Exception:
            done = False
        done_n += done
        rows.append((deadline, batch, name, done, note))

    # 下一個死線：未完成項中，死線 >= 今天的最早者；若全逾期則取最早逾期
    pending = [r for r in rows if not r[3]]
    next_dl = None
    if pending:
        future = sorted([r for r in pending if datetime.date(YEAR, *r[0]) >= TODAY], key=lambda r: r[0])
        overdue = sorted([r for r in pending if datetime.date(YEAR, *r[0]) < TODAY], key=lambda r: r[0])
        next_dl = (future[0] if future else overdue[0])

    lines = [f'# 素材狀態（{TODAY.isoformat()} 自動更新）', '']
    lines.append(f'**完成度：{done_n}／{len(rows)}**　')
    if next_dl:
        dl = datetime.date(YEAR, *next_dl[0])
        when = '今天' if dl == TODAY else ('已逾期' if dl < TODAY else f'{dl.month}/{dl.day}')
        lines.append(f'**下一個死線：{when} — {next_dl[2]}**（{next_dl[1]}）')
    else:
        lines.append('**全部完成 🎉**')
    lines += ['', '圖示：✅完成　⏰今天到期　⚠️逾期未完成　☐未到期', '']

    # 逾期 / 今天 置頂提醒
    urgent = [r for r in rows if not r[3] and datetime.date(YEAR, *r[0]) <= TODAY]
    if urgent:
        lines.append('## 🚨 現在該處理')
        for deadline, batch, name, done, note in sorted(urgent, key=lambda r: r[0]):
            dl = datetime.date(YEAR, *deadline)
            tag = '今天' if dl == TODAY else '逾期'
            lines.append(f'- {status_icon(done, deadline)} **{name}**（{tag}・{batch}）' + (f' — {note}' if note else ''))
        lines.append('')

    # 依批次列出
    lines.append('## 全部素材（依時程）')
    cur_batch = None
    for deadline, batch, name, done, note in rows:
        if batch != cur_batch:
            lines.append(f'\n### {batch}')
            cur_batch = batch
        lines.append(f'- {status_icon(done, deadline)} {name}' + (f' — {note}' if note else ''))

    # 成品與收件匣
    lines += ['', '## 成品（可直接複製貼出）']
    if rendered:
        for dst, remaining in rendered:
            tip = '（已全部代入）' if remaining == 0 else f'（尚有 {remaining} 個【佔位】，私訊的暱稱/當天小事屬正常保留）'
            lines.append(f'- 素材/成品/{dst} {tip}')
    if moved:
        lines += ['', '## 本次收件匣歸位']
        for name, sub in moved:
            lines.append(f'- {name} → 實品/{sub}/')

    # 本機原圖清點
    p1 = count_images(os.path.join(PHOTO_ROOT, '第一波_演出謝幕'))
    p2 = count_images(os.path.join(PHOTO_ROOT, '第二波_彩排幕後觀眾席'))
    lines += ['', '## 本機原圖資料夾（不進 git）',
              f'- `~/A4s音樂會素材原圖/第一波_演出謝幕/`：{p1} 張',
              f'- `~/A4s音樂會素材原圖/第二波_彩排幕後觀眾席/`：{p2} 張',
              '', '---', '*改值請編輯 `素材/提供資料.yaml` 後重跑 `python3 素材/update.py`。*']

    open(STATUS, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    return done_n, len(rows), next_dl


def main():
    for p in (INBOX, ACTUAL, OUT):
        os.makedirs(p, exist_ok=True)
    open(os.path.join(INBOX, '.gitkeep'), 'a').close()
    d = load_data()
    moved = route_inbox()
    rendered = render(d)
    done_n, total, next_dl = write_status(d, rendered, moved)

    print(f'✓ 成品已更新：素材/成品/（{len(rendered)} 份）')
    if moved:
        print(f'✓ 收件匣歸位 {len(moved)} 個檔案')
    print(f'✓ 進度 {done_n}/{total}，詳見 素材/狀態.md')
    if next_dl:
        dl = datetime.date(YEAR, *next_dl[0])
        when = '今天' if dl == TODAY else ('⚠️已逾期' if dl < TODAY else f'{dl.month}/{dl.day}')
        print(f'→ 下一個死線：{when} — {next_dl[2]}（{next_dl[1]}）')
    else:
        print('→ 全部完成 🎉')


if __name__ == '__main__':
    main()
