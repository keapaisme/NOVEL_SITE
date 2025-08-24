# pages/03_角色設定.py
import os, streamlit as st
# 先嘗試 Cloud 的 secrets，失敗就用本機 .env
def _load_env():
    try:
        os.environ.update({k: str(v) for k, v in st.secrets.items()})
    except Exception:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass
_load_env()

from utils.io_api import load_memory, save_memory

st.set_page_config(page_title="角色設定", page_icon="🧩", layout="wide")
st.title("🧩 角色設定 / 劇情旗標")

mem = load_memory()
tab1, tab2, tab3 = st.tabs(["角色字典", "劇情旗標", "拼寫規則"])

with tab1:
    st.caption("characters: 角色代碼 → {name, aliases, role}")
    new_char = st.text_input("新增角色代碼（如 HYH）", value="")
    if new_char and st.button("新增角色"):
        mem.setdefault("characters", {}).setdefault(new_char, {"name":"", "aliases":[], "role":""})
    to_del = []
    for code, info in mem.get("characters", {}).items():
        with st.expander(f"{code} / {info.get('name','')}"):
            info["name"] = st.text_input(f"{code} 名稱", value=info.get("name",""), key=f"n_{code}")
            aliases = st.text_input(f"{code} 別名（逗號分隔）", value=",".join(info.get("aliases",[])), key=f"a_{code}")
            info["aliases"] = [s.strip() for s in aliases.split(",") if s.strip()]
            info["role"] = st.text_input(f"{code} 角色定位", value=info.get("role",""), key=f"r_{code}")
            if st.button(f"刪除 {code}", key=f"d_{code}"):
                to_del.append(code)
    for c in to_del:
        mem["characters"].pop(c, None)

with tab2:
    st.caption("plot_flags: 任意布林/字串/數值都可")
    for k, v in list(mem.get("plot_flags", {}).items()):
        nv = st.text_input(k, value=str(v), key=f"pf_{k}")
        mem["plot_flags"][k] = nv
    new_k = st.text_input("新增旗標 key", key="pf_new_k")
    new_v = st.text_input("新增旗標 value", key="pf_new_v")
    if st.button("新增旗標"):
        mem.setdefault("plot_flags", {})[new_k] = new_v

with tab3:
    st.caption("spelling_rules: 錯別字、縮寫、渲染規則等")
    for k, v in list(mem.get("spelling_rules", {}).items()):
        nv = st.text_area(k, value=str(v), key=f"sr_{k}")
        mem["spelling_rules"][k] = nv
    new_sk = st.text_input("新增規則 key", key="sr_new_k")
    new_sv = st.text_area("新增規則 value", key="sr_new_v")
    if st.button("新增規則"):
        mem.setdefault("spelling_rules", {})[new_sk] = new_sv

if st.button("儲存", type="primary"):
    save_memory(mem)
    st.success("已寫入 data/memory.json")