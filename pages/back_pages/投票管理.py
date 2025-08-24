import streamlit as st
import json, os
from datetime import datetime

st.set_page_config(page_title="投票管理", layout="wide")
st.title("🛠️ 投票管理")

CFG_PATH = "data/vote_config.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(CFG_PATH):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump({"questions": []}, f, ensure_ascii=False, indent=2)

with open(CFG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)

st.subheader("現有題目")
for i, q in enumerate(cfg.get("questions", []), start=1):
    st.write(f"Q{i}. {q.get('question','(未命名)')}  ⏱️ 截止：{q.get('deadline','未設定')}")

st.markdown("---")
st.subheader("新增題目")
q_text = st.text_input("題目內容")
opts = st.text_area("選項（每行一個）").strip().splitlines()
deadline = st.text_input("截止時間（YYYY-MM-DD HH:MM，可留空）")

if st.button("➕ 新增題目", use_container_width=True):
    if not q_text or not opts:
        st.error("請輸入題目與至少一個選項")
    else:
        try:
            if deadline:
                datetime.strptime(deadline, "%Y-%m-%d %H:%M")
        except ValueError:
            st.error("截止時間格式錯誤")
        else:
            cfg.setdefault("questions", []).append({
                "question": q_text,
                "options": opts,
                "deadline": deadline if deadline else None
            })
            with open(CFG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            st.success("已新增題目！")
            st.rerun()

st.markdown("---")
st.subheader("關閉題目（立即截止）")
idx = st.number_input("輸入要關閉的題目編號", min_value=1, step=1)
if st.button("⏹️ 關閉題目", use_container_width=True):
    qs = cfg.get("questions", [])
    if 1 <= idx <= len(qs):
        qs[idx-1]["deadline"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        st.success(f"已關閉 Q{idx}")
        st.rerun()
    else:
        st.error("題目編號不存在")