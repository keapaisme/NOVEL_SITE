# 📅 整理時間：2025-08-22 23:58
# 🛠️ 功能說明：讀取 summaries.json 並根據檔名查詢指定章節摘要資訊
# 🧾 用途：給投票模組、自動分支推進模組等模組做摘要查詢用途

import json
from pathlib import Path
from typing import Optional, Dict

SUMMARY_PATH = Path("data/summaries.json")

def load_summaries(path: Path = SUMMARY_PATH) -> Dict:
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            return {}
    return {}

def get_summary_by_filename(filename: str, path: Path = SUMMARY_PATH) -> Optional[dict]:
    data = load_summaries(path)
    return data.get(filename)
