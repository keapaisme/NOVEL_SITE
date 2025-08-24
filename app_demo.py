# app_demo.py
# 🗓️ 生成時間：2025-08-24 01:49:40
# 📌 程式功能：主控 Streamlit UI，整合章節生成、投票提交與摘要顯示等功能
# 🧾 來源：用戶要求重建檔案（原檔誤刪），依照 A1～A5 整合版本製作

import streamlit as st
from pathlib import Path
import json
from datetime import datetime
from utils.io_api import list_chapters, read_chapter
from utils.vote_logger import log_vote
from utils.append_vote_question import _safe_load_vote_cfg

st.set_page_config(page_title="AI小說平台 DEMO", page_icon="📖", layout="wide")
st.title("📖 AI小說展示平台 DEMO")

CH_DIR = Path("data/chapters_md")

# ---------- 顯示最新章節 ----------
items = list_chapters()
if not items:
    st.warning("⚠️ 尚無章節資料")
    st.stop()

latest = sorted(items, key=lambda x: x['id'] if isinstance(x, dict) else str(x))[-1]
ch_id = latest["id"] if isinstance(latest, dict) else str(latest)

st.header(f"📘 最新章節：{ch_id}")
try:
    st.markdown(read_chapter(ch_id))
except Exception as e:
    st.error(f"無法讀取章節檔案：{e}")

# ---------- 顯示投票選項（若存在） ----------
vote_cfg = _safe_load_vote_cfg()
vote_node = None
for q in vote_cfg.get("questions", [])[::-1]:  # 倒序尋找對應章節
    if q.get("chapter_id") == ch_id:
        vote_node = q
        break

if vote_node:
    st.divider()
    st.subheader("🗳️ 讀者投票")
    st.markdown(f"**{vote_node['question']}**")
    selected = st.radio("請選擇一項：", vote_node["options"], key="vote_choice")

    if st.button("提交投票", type="primary"):
        log_vote(ch_id, selected)
        st.success("✅ 投票成功！感謝你的參與！")
else:
    st.info("📭 本章尚無投票")

# ---------- 結尾 ----------
st.divider()
st.caption("© Novel Lite DEMO 介面  | Powered by Streamlit + ChatGPT")

