# -*- coding: utf-8 -*-
"""小編任務 Checklist 網頁（Streamlit）。

給很忙、眼力不好的小編用：大字、高對比、可調字級、點一下就打勾。
進度存放：本機跑 → 素材/小編進度.json；部署到 Streamlit Cloud → Google 試算表
（自動切換，見 progress_store.py 與 素材/上線到StreamlitCloud教學.md）。

本機啟動（在專案根目錄）：
    streamlit run 素材/小編checklist.py
"""
import os
import sys
import datetime

import yaml
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import progress_store  # noqa: E402

TASKS_FILE = os.path.join(HERE, '小編任務.yaml')
YEAR = 2026


# ────────────────────────── 資料 ──────────────────────────
def load_tasks():
    with open(TASKS_FILE, encoding='utf-8') as f:
        return (yaml.safe_load(f) or {}).get('階段', [])


def d(mmdd):
    m, day = mmdd.split('-')
    return datetime.date(YEAR, int(m), int(day))


def now_str():
    return datetime.datetime.now().strftime('%m/%d %H:%M')


phases = load_tasks()
all_tasks = [t for ph in phases for t in ph['任務']]
LABELS = {t['id']: t['做'] for t in all_tasks}   # 寫進試算表時順便存可讀文字


# ────────────────────────── 點擊處理 ──────────────────────────
def toggle(tid):
    prog = progress_store.load()
    if st.session_state.get(f'cb_{tid}'):
        prog[tid] = {'done': True, 'ts': now_str()}
    else:
        prog.pop(tid, None)
    progress_store.save(prog, LABELS)


# ────────────────────────── 版面 ──────────────────────────
st.set_page_config(page_title='小編任務清單', page_icon='✅', layout='centered')

size = st.sidebar.radio('字級', ['大', '特大', '超大'], index=1)
BASE = {'大': 20, '特大': 26, '超大': 32}[size]
st.sidebar.caption('做完一項就點一下方框。\n點了會自動記錄，關掉網頁也不會掉。')
st.sidebar.caption(f'進度存放：{progress_store.backend_name()}')

st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"], .stApp {{ font-size: {BASE}px; }}
  [data-testid="stMarkdownContainer"] p {{ font-size: {BASE}px !important; line-height: 1.55 !important; }}
  .stCheckbox label {{ min-height: 2.0em; padding: .3rem 0; align-items: center; }}
  .stCheckbox label p {{ font-size: {BASE}px !important; line-height: 1.5 !important; }}
  .stCheckbox [data-baseweb="checkbox"] > div:first-child {{ transform: scale(1.6); margin-right: .7rem; }}
  .stCheckbox {{ margin-bottom: .5rem; }}
  h1 {{ font-size: {BASE + 14}px !important; }}
  h2, [data-testid="stHeading"] h2 {{ font-size: {BASE + 6}px !important; }}
  [data-testid="stExpander"] summary p {{ font-size: {BASE + 2}px !important; }}
  .why  {{ color:#5f5f5f; font-size:{BASE - 4}px; margin: -.2rem 0 .2rem 3rem; }}
  .give {{ color:#0a7d3c; font-size:{BASE - 4}px; margin: -.05rem 0 .2rem 3rem; }}
  .donetime {{ color:#0a7d3c; font-size:{BASE - 5}px; margin: -.15rem 0 .35rem 3rem; }}
  .block-container {{ padding-top: 2rem; max-width: 840px; }}
</style>
""", unsafe_allow_html=True)

today = datetime.date.today()

# session_state 從存檔初始化（避免覆蓋使用者剛點的）
prog = progress_store.load()
for t in all_tasks:
    k = f"cb_{t['id']}"
    if k not in st.session_state:
        st.session_state[k] = prog.get(t['id'], {}).get('done', False)

# 點擊回呼已寫入存檔，這裡重讀一次，確保數字與「已完成時間」即時更新
prog = progress_store.load()

total = len(all_tasks)
done = sum(1 for t in all_tasks if prog.get(t['id'], {}).get('done'))

st.title('✅ 小編任務清單')
st.caption(f"今天 {today.month}/{today.day}　做完一項就點方框，會自動記錄")
st.progress(done / total if total else 0)
st.markdown(f"### 進度 {done} / {total}")

pending_phases = [ph for ph in phases
                  if any(not prog.get(t['id'], {}).get('done') for t in ph['任務'])]
upcoming = sorted([ph for ph in pending_phases if d(ph['迄']) >= today], key=lambda p: d(p['起']))
overdue = sorted([ph for ph in pending_phases if d(ph['迄']) < today], key=lambda p: d(p['起']))
if overdue:
    st.error(f"⚠️ 有逾期還沒做完：{overdue[0]['標題']}")
elif upcoming:
    nx = upcoming[0]
    when = '今天' if d(nx['起']) <= today <= d(nx['迄']) else f"{d(nx['起']).month}/{d(nx['起']).day}"
    st.info(f"下一個：{when}　{nx['標題']}")
else:
    st.success('全部完成 🎉 辛苦了！')


def render_task(t):
    tid = t['id']
    st.checkbox(t['做'], key=f'cb_{tid}', on_change=toggle, args=(tid,))
    rec = prog.get(tid, {})
    if t.get('為什麼'):
        st.markdown(f"<div class='why'>↳ {t['為什麼']}</div>", unsafe_allow_html=True)
    if t.get('交件'):
        st.markdown(f"<div class='give'>📤 {t['交件']}</div>", unsafe_allow_html=True)
    if rec.get('done') and rec.get('ts'):
        st.markdown(f"<div class='donetime'>✔ 已完成 {rec['ts']}</div>", unsafe_allow_html=True)


# 今天 / 逾期未完成 置頂
st.markdown('---')
hot = []
for ph in phases:
    is_today = d(ph['起']) <= today <= d(ph['迄'])
    is_overdue = d(ph['迄']) < today
    for t in ph['任務']:
        undone = not prog.get(t['id'], {}).get('done')
        if is_today or (is_overdue and undone):
            hot.append((ph, t, is_overdue and undone))

shown_ids = set()
if hot:
    st.header('🔴 現在該做的')
    for ph, t, od in hot:
        if od:
            st.caption(f"（逾期・{ph['標題']}）")
        render_task(t)
        shown_ids.add(t['id'])   # 同一任務只渲染一次，避免重複 checkbox key
else:
    st.header('今天沒有指定任務 👍')

# 全部（依階段，今天的自動展開）；已在上方顯示過的不再放 checkbox
st.markdown('---')
st.header('全部任務')
for ph in phases:
    is_today = d(ph['起']) <= today <= d(ph['迄'])
    ph_done = sum(1 for t in ph['任務'] if prog.get(t['id'], {}).get('done'))
    ph_total = len(ph['任務'])
    mark = '✅' if ph_done == ph_total else ('🔴' if ph.get('急迫') else '')
    label = f"{mark} {ph['標題']}　（{ph_done}/{ph_total}）"
    with st.expander(label, expanded=is_today):
        rendered_here = 0
        for t in ph['任務']:
            if t['id'] in shown_ids:
                continue
            render_task(t)
            rendered_here += 1
        if rendered_here == 0:
            st.caption('這個階段的項目已列在上方「🔴 現在該做的」。')

st.markdown('---')
st.caption('產出的截圖、照片、影片請走原本的管道（共用資料夾／LINE 相簿），不用上傳這裡。')
