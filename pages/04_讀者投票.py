# 📁 04_讀者投票.py
# 📅 更新時間：2025-08-22 23:05
# 📌 功能：展示投票題目，接收選項點選，並寫入 vote_log.json（整合 A3 模組）

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from utils.vote_logger import log_vote  # ✅ 整合 A3

CFG_PATH = Path("data/vote_config.json")

# --- 載入資料 ---
if not CFG_PATH.exists():
    st.error("找不到投票題目設定檔 vote_config.json")
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

# --- 顯示題目列表 ---
st.title("📊 讀者投票題目紀錄（後台版）")

for q in reversed(questions):
    chapter = q.get("chapter_id", "?")
    question = q.get("question", "?")
    options = q.get("options", [])
    deadline = q.get("deadline", "?")

    with st.expander(f"📘 {chapter}：{question}"):
        st.caption(f"🕒 投票截止：{deadline}")
        selected = st.radio("請選擇：", options, key=chapter)

        if st.button("✅ 提交投票", key=f"submit_{chapter}"):
            try:
                log_vote(chapter, selected, user_id="anonymous")
                st.success(f"你選擇了：{selected}，記錄成功 ✅")
            except Exception as e:
                st.error(f"❌ 記錄失敗：{e}")
