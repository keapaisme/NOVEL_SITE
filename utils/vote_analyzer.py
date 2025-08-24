# 📅 建立時間：2025-08-23
# 🧠 功能：統計指定章節的投票結果，回傳得票最多的選項
# 🧾 用途：用於 A7 自動根據投票結果續寫劇情分支

import json
from collections import Counter
from pathlib import Path

LOG_PATH = Path("data/vote_log.json")

def analyze_votes(chapter_id: str) -> dict:
    """
    分析某章節的投票紀錄，回傳最多票的選項。
    """
    if not LOG_PATH.exists():
        return {}

    try:
        logs = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        votes = [v["option"] for v in logs if v.get("chapter_id") == chapter_id]
        if not votes:
            return {}
        counter = Counter(votes)
        top = counter.most_common(1)[0]
        return {"top": top[0], "count": top[1], "all": dict(counter)}
    except Exception as e:
        return {"error": str(e)}

def get_vote_winner(chapter_id: str) -> str:
    """
    回傳指定章節的最高得票選項；若沒有紀錄或平手，回傳空字串
    """
    if not LOG_PATH.exists():
        return ""

    try:
        logs = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return ""

    votes = [log["selected"] for log in logs if log.get("chapter_id") == chapter_id]
    if not votes:
        return ""

    counter = Counter(votes)
    top = counter.most_common()
    if len(top) == 1 or (len(top) >= 2 and top[0][1] > top[1][1]):
        return top[0][0]  # 單一最高票
    else:
        return ""  # 平手或無明確勝者
