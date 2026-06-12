# -*- coding: utf-8 -*-
"""小編進度的存取後端，給 小編checklist.py 與 update.py 共用。

依 st.secrets 自動選後端（找到一個能用的就用，否則退到下一個）：
  ‣ checklist_webapp_url（＋checklist_token）→ 走 Google Apps Script Web App（方案 B，不用服務帳號）
  ‣ gcp_service_account（＋progress_sheet_id）→ 走 gspread 直連試算表（方案 A，需服務帳號）
  ‣ 都沒有 → 讀寫本機 素材/小編進度.json（自己電腦跑，零設定）

任何雲端失敗都退回本機檔，盡量不掉資料。
"""
import os
import json
import datetime
import urllib.request
import urllib.parse

TZ8 = datetime.timezone(datetime.timedelta(hours=8))   # 台灣時間

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(HERE, '小編進度.json')
WS_TITLE = '進度'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
HTTP_TIMEOUT = 12

_WS = None  # gspread worksheet 只在成功後快取


# ───────────────── 方案 B：Apps Script Web App ─────────────────
def _webapp():
    try:
        import streamlit as st
        url = st.secrets['checklist_webapp_url']
        token = st.secrets.get('checklist_token', '')
        return (url, token) if url else None
    except Exception:
        return None


def _fmt_ts(ts):
    """試算表可能把時間字串自動轉成 ISO 日期；統一轉回 MM/DD HH:MM（台灣時間）。"""
    s = str(ts or '')
    if 'T' in s:
        try:
            dt = datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(TZ8).strftime('%m/%d %H:%M')
        except Exception:
            return s
    return s


def _webapp_load(url, token):
    full = url + ('&' if '?' in url else '?') + 'token=' + urllib.parse.quote(token)
    with urllib.request.urlopen(full, timeout=HTTP_TIMEOUT) as r:
        data = json.loads(r.read().decode('utf-8'))
    if not isinstance(data, dict) or 'error' in data:
        raise ValueError('webapp load error')
    return {k: {'done': True, 'ts': _fmt_ts((v or {}).get('ts', ''))}
            for k, v in data.items() if isinstance(v, dict) and v.get('done')}


def _webapp_save(url, token, prog, labels):
    payload = json.dumps({'token': token, 'progress': prog, 'labels': labels or {}}).encode('utf-8')
    req = urllib.request.Request(url, data=payload,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    urllib.request.urlopen(req, timeout=HTTP_TIMEOUT).read()


# ───────────────── 方案 A：gspread 直連 ─────────────────
def _worksheet():
    global _WS
    if _WS is not None:
        return _WS
    try:
        import streamlit as st
        gcp = dict(st.secrets['gcp_service_account'])
        sheet_id = st.secrets['progress_sheet_id']
    except Exception:
        return None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(gcp, scopes=SCOPES)
        sh = gspread.authorize(creds).open_by_key(sheet_id)
        try:
            _WS = sh.worksheet(WS_TITLE)
        except Exception:
            _WS = sh.add_worksheet(WS_TITLE, rows=200, cols=4)
            _WS.append_rows([['task_id', 'done', 'ts', '任務']], value_input_option='RAW')
        return _WS
    except Exception:
        return None   # 暫時失敗不快取，下次重試


# ───────────────── 對外 ─────────────────
def load():
    wa = _webapp()
    if wa:
        try:
            return _webapp_load(*wa)
        except Exception:
            pass
    ws = _worksheet()
    if ws is not None:
        try:
            prog = {}
            for r in ws.get_all_records():
                if str(r.get('done')).upper() in ('TRUE', '1', '✓', 'YES'):
                    prog[str(r.get('task_id'))] = {'done': True, 'ts': str(r.get('ts', ''))}
            return prog
        except Exception:
            pass
    if os.path.exists(LOCAL):
        try:
            return json.load(open(LOCAL, encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save(prog, labels=None):
    wa = _webapp()
    if wa:
        try:
            _webapp_save(*wa, prog, labels)
            return
        except Exception:
            pass
    ws = _worksheet()
    if ws is not None:
        try:
            rows = [['task_id', 'done', 'ts', '任務']]
            for tid, v in prog.items():
                if v.get('done'):
                    rows.append([tid, 'TRUE', v.get('ts', ''), (labels or {}).get(tid, '')])
            ws.clear()
            ws.append_rows(rows, value_input_option='RAW')
            return
        except Exception:
            pass
    json.dump(prog, open(LOCAL, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def backend_name():
    if _webapp():
        return 'Google 試算表（Apps Script）'
    if _worksheet() is not None:
        return 'Google 試算表（服務帳號）'
    return '本機檔'
