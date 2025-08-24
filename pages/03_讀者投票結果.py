# 📄 檔案名稱：03_讀者投票結果.py
# 📅 建立時間：2025-08-23
# 🧾 用途：展示目前所有的集中式投票題目與截止時間，供讀者查看

import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="讀者投票結果", layout="wide")
st.title("📊 讀者投票結果一覽")

CFG_PATH = Path("data/vote_config.json")

# --- 載入資料 ---
if not CFG_PATH.exists():
    st.error("找不到投票設定檔 vote_config.json")
    st.stop()

try:
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
except Exception as e:
    st.error(f"vote_config.json 解析失敗：{e}")
    st.stop()

questions = cfg.get("questions", [])
if not questions:
    st.info("目前尚無任何投票題目。")
    st.stop()

# --- 顯示所有投票題目 ---
for q in reversed(questions):
    chapter = q.get("chapter_id", "?")
    question = q.get("question", "?")
    options = q.get("options", [])
    deadline = q.get("deadline", "未設定")

    with st.expander(f"📘 {chapter}：{question}"):
        st.caption(f"🕒 截止時間：{deadline}")
        for opt in options:
            st.markdown(f"- {opt}")
