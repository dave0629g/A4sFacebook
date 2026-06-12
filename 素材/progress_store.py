# -*- coding: utf-8 -*-
"""小編進度的存取後端，給 小編checklist.py 與 update.py 共用。

兩種模式自動切換：
  ‣ 有設定 Google 試算表（st.secrets 內含 gcp_service_account ＋ progress_sheet_id）
    → 讀寫雲端試算表（部署到 Streamlit Cloud 用這個，耐重啟、搭檔與 Claude 都讀得到）
  ‣ 否則 → 讀寫本機 素材/小編進度.json（自己電腦跑用這個，零設定）

任何雲端失敗都會退回本機檔，盡量不掉資料。
"""
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(HERE, '小編進度.json')
WS_TITLE = '進度'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

_WS = None   # 只在「成功拿到 worksheet」後才快取；連線暫時失敗不 latch，下次互動會重試


def _worksheet():
    """回傳 Google 試算表 worksheet；沒設定或失敗則回 None（用本機檔）。"""
    global _WS
    if _WS is not None:
        return _WS
    # 讀 secrets（雲端在 dashboard 設定；本機放 .streamlit/secrets.toml 才會有）
    try:
        import streamlit as st
        gcp = dict(st.secrets['gcp_service_account'])
        sheet_id = st.secrets['progress_sheet_id']
    except Exception:
        return None   # 沒設定 secrets → 本機模式（重判很便宜，不快取）
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
        return None   # 連線暫時失敗 → 不快取，下次互動再試（避免被永久鎖在本機）


def load():
    """回傳 {task_id: {'done': True, 'ts': '...'}}。"""
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
    """存進度。labels={task_id: 任務文字} 會多寫一欄方便人看。"""
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
            pass  # 退回本機，至少不掉
    json.dump(prog, open(LOCAL, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def backend_name():
    return 'Google 試算表（雲端）' if _worksheet() is not None else '本機檔'
