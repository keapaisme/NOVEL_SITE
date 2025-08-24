# utils/vote_logger.py
from pathlib import Path
from datetime import datetime
import json, os

LOG_PATH = Path("data/vote_log.json")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def _load_logs():
    """容錯讀取，支援 list 或 {'logs': [...]}，壞檔自動重置。"""
    if not LOG_PATH.exists():
        return []
    try:
        data = json.loads(LOG_PATH.read_text("utf-8"))
    except Exception:
        return []
    # 歷史兩種格式容錯
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("logs", [])
    return []

def _save_logs(logs: list):
    """統一存成純 list（最簡單）。"""
    LOG_PATH.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")

def log_vote(chapter_id: str, selected: str, user_id: str = "anonymous"):
    """追加一筆投票紀錄。"""
    logs = _load_logs()
    logs.append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "chapter_id": chapter_id,
        "selected": selected,
        "user_id": user_id
    })
    _save_logs(logs)