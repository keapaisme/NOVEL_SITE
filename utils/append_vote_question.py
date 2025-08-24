# 📅 重寫時間：2025-08-22 23:59
# 🛠️ 功能說明：每隔 3 章，從 summaries.json 中提取摘要並自動生成讀者投票題目寫入 vote_config.json
# 🧾 用途：整合原投票模組與 summaries.json，避免重複開讀 md 文章，提升穩定性與效率

import json
from datetime import datetime, timedelta
from pathlib import Path
from summary_utils import get_summary_by_filename

ROOT = Path(__file__).parent.parent
SUMMARY_PATH = ROOT / "tools" / "data" / "summaries.json"
VOTE_CFG_PATH = ROOT / "data" / "vote_config.json"

def _safe_load_vote_cfg() -> dict:
    if not VOTE_CFG_PATH.parent.exists():
        VOTE_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not VOTE_CFG_PATH.exists() or not VOTE_CFG_PATH.read_text(encoding="utf-8").strip():
        base = {"questions": []}
        VOTE_CFG_PATH.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
        return base
    try:
        return json.loads(VOTE_CFG_PATH.read_text(encoding="utf-8"))
    except Exception:
        base = {"questions": []}
        VOTE_CFG_PATH.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
        return base

def _append_vote_question(chapter_id: str, chapter_md: str):
    try:
        idx = int(str(chapter_id).split("_")[-1])
    except Exception:
        return

    if idx % 3 != 0:
        return

    # 收集最近三章摘要
    briefs = []
    for i in range(max(1, idx-2), idx+1):
        filename = f"第{i:02d}章"
        matched = [k for k in get_summary_by_filename.__globals__["load_summaries"](SUMMARY_PATH) if filename in k]
        if matched:
            info = get_summary_by_filename(matched[0], SUMMARY_PATH)
            briefs.append({"id": filename, "brief": info.get("summary", "")})

    context_json = json.dumps(briefs, ensure_ascii=False)

    # 模擬 GPT 投票題（這裡簡化，實際可改為 call GPT）
    question = f"針對最近章節，下一步劇情應該怎麼走？"
    options = ["A. 情節升溫", "B. 對手反擊", "C. 出現新人物"]

    deadline = (datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)
                + timedelta(days=7)).strftime("%Y-%m-%d %H:%M")

    cfg = _safe_load_vote_cfg()
    cfg.setdefault("questions", []).append({
        "chapter_id": chapter_id,
        "question": question,
        "options": options[:5],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "deadline": deadline
    })
    VOTE_CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
