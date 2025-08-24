# 📄 01_生成新章節.py
# 🧠 功能：手動輸入提示 → GPT 生成 Markdown 章節
# ✅ 整合 A5（投票產生）、A6（截止限制）、A7（投票分析）、A8（旗標 UI）、A9（票選提示注入）

from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os, json, time
from typing import List, Dict, Any
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from utils.io_api import (
    load_style, load_outline, load_memory, write_chapter,
    list_chapters, read_chapter, save_memory
)
from utils.append_vote_question import _safe_load_vote_cfg, _append_vote_question
from utils.vote_analyzer import get_vote_winner  # ✅ A7/A9

# ---------- 環境變數 ----------
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ---------- 頁面設定 ----------
st.set_page_config(page_title="生成新章節 / 文章", page_icon="📝", layout="wide")
st.title("📝 生成新章節 / 文章")

# ---------- 路徑 ----------
ROOT = Path(__file__).resolve().parents[1]
CH_DIR = ROOT / "data" / "chapters_md"; CH_DIR.mkdir(parents=True, exist_ok=True)
CACHE_OUT = ROOT / "data" / "cache" / "outlines_cache.json"
OUTLINE_JSON = ROOT / "data" / "chapter_outlines.json"

# ---------- 資料 ----------
style = load_style()
_ = load_outline()
memory = load_memory()

# ---------- 公用工具 ----------
def _safe_read(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
    except Exception:
        return default

def load_outline_for(chapter_id: str):
    oc = _safe_read(CACHE_OUT, {})
    co = _safe_read(OUTLINE_JSON, {})
    if isinstance(oc, dict) and chapter_id in oc: return oc[chapter_id]
    if isinstance(co, dict) and chapter_id in co: return co[chapter_id]
    return {}

def prev_outline_context(chapter_id: str, k: int = 3) -> List[Dict[str, Any]]:
    try:
        idx = int(str(chapter_id).split("_")[-1])
    except Exception:
        return []
    out = []
    for i in range(max(1, idx - k), idx):
        key = f"ch_{i:03d}"
        node = load_outline_for(key)
        if not node: continue
        title = node.get("title") or node.get("name") or node.get("chapter_title")
        bullets = node.get("bullets") or node.get("summary") or []
        if isinstance(bullets, str): bullets = [bullets]
        out.append({"id": key, "title": title, "bullets": bullets[:5]})
    return out

def prev_context(chapter_id: str, k: int = 3, limit_chars: int = 1500):
    try:
        idx = int(str(chapter_id).split("_")[-1])
    except Exception:
        return []
    ctx = []
    for i in range(max(1, idx - k), idx):
        p = CH_DIR / f"ch_{i:03d}.md"
        if p.exists():
            text = p.read_text(encoding="utf-8")
            ctx.append({"id": f"ch_{i:03d}", "brief": text[:limit_chars]})
    return ctx

# ---------- 章節ID推算 ----------
def _next_ch_id():
    items = list_chapters() or []
    ids = []
    for it in items:
        cid = it["id"] if isinstance(it, dict) else str(it)
        if cid.startswith("ch_"):
            try: ids.append(int(cid.split("_")[-1]))
            except Exception: pass
    return f"ch_{(max(ids)+1 if ids else 1):03d}"

# ---------- 輸入欄 ----------
col1, col2 = st.columns(2)
with col1:
    ch_id = st.text_input("章節ID（檔名不含 .md）", value=_next_ch_id())
with col2:
    subtitle = st.text_input("副標題（可留空）", value="")
seed = st.text_area("提示/走向（可留空）", height=140,
                    placeholder="寫場景、衝突、視角、收尾…")

# ✅ A9：讀者票選提示（可選）
use_vote_seed = st.checkbox("使用讀者票選結果作為劇情走向提示", value=True)

# ---------- 進階設定 ----------
with st.expander("進階設定：連貫性與旗標", expanded=True):
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        use_recent = st.checkbox("加入最近幾章摘要", value=True)
        use_outline = st.checkbox("加入最近幾章大綱摘要", value=True)
    with c2:
        recent_k = st.slider("前置章節數", 1, 3, 3)
    with c3:
        ctx_limit = st.select_slider("摘要字數上限", [800,1200,1500,2000], value=1500)
    flags_note = st.text_area("本章劇情旗標變更（可留空，JSON 或 key=value, 逗號分隔）", height=80)
    max_tokens = st.number_input("最大輸出 tokens", 500, 8000, 2000, 100)
    show_debug = st.checkbox("顯示除錯訊息", value=False)

# ---------- 投票截止限制（A6 集中式） ----------
vote_cfg = _safe_load_vote_cfg()
vote_node = None
for q in vote_cfg.get("questions", [])[::-1]:
    if q.get("chapter_id") == ch_id:
        vote_node = q
        break

vote_locked = False
deadline_str = None
if vote_node:
    deadline_str = vote_node.get("deadline")
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
        vote_locked = datetime.now() < deadline
    except Exception as e:
        st.warning(f"❗ 投票時間格式錯誤：{e}")

# ---------- 構建 GPT messages ----------
def build_messages(chapter_id: str, seed_final: str) -> list[dict]:
    sys_prompt = (
        "你是一位中文小說作者。只輸出 Markdown 正文，不要解釋。"
        "嚴格維持角色姓名、稱謂、既有關係與已發生事件的一致性；不得推翻已確立的劇情旗標。"
    )
    outline_this = load_outline_for(chapter_id)
    ctx = prev_context(chapter_id, k=recent_k, limit_chars=int(ctx_limit)) if use_recent else []
    ctx_outline = prev_outline_context(chapter_id, k=recent_k) if use_outline else []

    return [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": json.dumps({
            "chapter_id": chapter_id,
            "subtitle": subtitle,
            "seed": seed_final,
            "style_profile": style,
            "memory": memory,
            "outline_current": outline_this,
            "recent_context": ctx,
            "recent_outline": ctx_outline,
            "consistency_rules": [
                "角色姓名與稱謂不得變更",
                "已揭示的人物關係與祕密不得反轉",
                "承接上一章的懸念並在本章推進",
            ],
        }, ensure_ascii=False)},
    ]

# ---------- GPT 生成 ----------
def generate_markdown(chapter_id: str, seed_final: str) -> tuple[str, str]:
    msgs = build_messages(chapter_id, seed_final)
    text_input = "\n\n".join(f"{m['role']}: {m['content']}" for m in msgs)

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    dbg = [f"model={model}", f"max_output_tokens={int(max_tokens)}",
           f"use_recent={use_recent}", f"use_outline={use_outline}",
           f"recent_k={recent_k}", f"ctx_limit={ctx_limit}"]

    # 嘗試一次
    try:
        resp = client.responses.create(
            model=model,
            input=text_input,
            max_output_tokens=int(max_tokens),
        )
        out = getattr(resp, "output_text", "") or ""
        dbg.append(f"try1_empty={len(out.strip())==0}")
        if out.strip():
            return out, "\n".join(dbg)
    except Exception as e:
        dbg.append(f"try1_err={type(e).__name__}: {e}")
        # 型號/限流 → 回退一次
        if model != "gpt-4o-mini":
            try:
                time.sleep(2)
                resp_fb = client.responses.create(
                    model="gpt-4o-mini",
                    input=text_input,
                    max_output_tokens=int(max_tokens),
                )
                out_fb = getattr(resp_fb, "output_text", "") or ""
                dbg.append("fallback_to=gpt-4o-mini")
                if out_fb.strip():
                    return out_fb, "\n".join(dbg)
            except Exception as e2:
                dbg.append(f"fallback_err={type(e2).__name__}: {e2}")

    # 簡化重試（保底）
    simple_input = (
        "system: 你是一位中文小說作者，輸出純 Markdown 章節內容，不要解釋。\n\n"
        f"user: 章節ID={chapter_id} 副標題={subtitle}\n"
        f"seed: {seed_final or '請以主要角色視角寫一段有事件起迄的劇情，1200~1800字。'}\n"
        "規範: 1) 直接輸出正文；2) 不要附任何說明；3) 如使用標題，置於第一行。"
    )
    try:
        time.sleep(1.5)
        resp2 = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=simple_input,
            max_output_tokens=int(max_tokens),
        )
        out2 = getattr(resp2, "output_text", "") or ""
        dbg.append(f"try2_empty={len(out2.strip())==0}")
        return out2, "\n".join(dbg)
    except Exception as e2:
        dbg.append(f"try2_err={type(e2).__name__}: {e2}")
        return "", "\n".join(dbg)

# ---------- 執行按鈕 ----------
if st.button("生成", type="primary"):
    if vote_locked and not st.checkbox("🛠️ 後台強制跳過投票截止限制"):
        st.warning(f"⚠️ 尚未達到投票截止時間（{deadline_str}），暫不可生成新章節")
        st.stop()

    if not ch_id.strip():
        st.error("章節ID不可為空")
        st.stop()

    # ✅ 注入投票結果提示（上一章的勝出選項）
    vote_msg = ""
    try:
        last_idx = int(ch_id.split("_")[-1]) - 1
        if last_idx >= 1:
            last_id = f"ch_{last_idx:03d}"
            winner = get_vote_winner(last_id)
            if use_vote_seed and winner:
                vote_msg = f"【讀者票選結果】上一章後大家選擇了：{winner}\n"
    except Exception:
        pass
    seed_final = f"{vote_msg}{seed or ''}".strip()

    with st.spinner("生成中…"):
        md, dbg = generate_markdown(ch_id.strip(), seed_final)

    if show_debug:
        with st.expander("debug"):
            st.code(dbg)

    if not md or not md.strip():
        st.warning("生成失敗，請稍後再試或檢查 debug 訊息")
        st.stop()

    if subtitle and not md.lstrip().startswith("#"):
        md = f"# {ch_id} · {subtitle}\n\n{md}"

    write_chapter(ch_id.strip(), md)
    st.success(f"✅ 已寫入：data/chapters_md/{ch_id}.md")
    st.markdown(md)

    # ✅ A5：每 3 章自動產生投票題
    try:
        _append_vote_question(ch_id.strip(), md)
        st.info("✅ 已自動產生投票題（每 3 章一次）")
    except Exception as e:
        st.warning(f"⚠️ 投票題自動產生失敗：{e}")

    # ✅ A8：寫回 plot_flags（若提供）
    if flags_note.strip():
        try:
            upd = {}
            txt = flags_note.strip()
            if txt.startswith("{"):
                upd = json.loads(txt)
            else:
                for pair in txt.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        k = k.strip(); v = v.strip()
                        if v.lower() in ("true", "false"):
                            v = v.lower() == "true"
                        elif v.isdigit():
                            v = int(v)
                        elif v.startswith(("'", '"')) and v.endswith(("'", '"')):
                            v = v[1:-1]
                        upd[k] = v
            mem2 = load_memory()
            pf = mem2.setdefault("plot_flags", {})
            pf.update(upd)
            pf["_last_update"] = datetime.now().isoformat(timespec="seconds")
            save_memory(mem2)
            st.success("✅ 已更新 memory.json 的 plot_flags")
        except Exception as e:
            st.warning(f"⚠️ flag 更新失敗：{e}")

# ---------- 參考上一章 ----------
st.divider()
st.subheader("📖 參考上一章")
items = list_chapters() or []
if items:
    def _get_id(x): return x["id"] if isinstance(x, dict) else str(x)
    last_id = sorted(items, key=_get_id)[-1]; last_id = _get_id(last_id)
    if st.checkbox(f"顯示 {last_id}.md"):
        try:
            st.code(read_chapter(last_id), language="markdown")
        except Exception as e:
            st.caption(f"讀取失敗：{e}")