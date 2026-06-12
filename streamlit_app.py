# -*- coding: utf-8 -*-
"""Streamlit Community Cloud 進入點。

部署時 main file path 填 streamlit_app.py 即可（這支會去跑 素材/小編checklist.py）。
本機要跑也可以直接： streamlit run 素材/小編checklist.py

註：內層透過 runpy 載入，不享有 Streamlit 的 magic 自動顯示，
    小編checklist.py 一律用顯式 st.write/st.markdown（目前都是），勿依賴裸運算式輸出。
"""
import os
import sys
import runpy

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(ROOT, '素材', '小編checklist.py')
sys.path.insert(0, os.path.join(ROOT, '素材'))   # 讓 progress_store 可被 import
runpy.run_path(APP, run_name='__main__')
