from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CH_DIR = ROOT / "data" / "chapters_md"
STYLE_PATH = ROOT / "data" / "style_profile.json"
OUTLINE_PATH = ROOT / "data" / "chapter_outlines.json"
MEM_PATH = ROOT / "data" / "memory.json"
VOTE_DIR = ROOT / "data" / "votes"
LOG_DIR = ROOT / "novel_logs"

CH_DIR.mkdir(parents=True, exist_ok=True)
VOTE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def _read_json(p: Path, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def _write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def list_chapters():
    items = []
    for p in sorted(CH_DIR.glob("*.md")):
        items.append({"id": p.stem, "path": str(p), "name": p.stem})
    return items

def read_chapter(ch_id: str) -> str:
    p = CH_DIR / f"{ch_id}.md" if not ch_id.endswith(".md") else CH_DIR / ch_id
    return p.read_text(encoding="utf-8")

def write_chapter(ch_id: str, md: str):
    p = CH_DIR / f"{ch_id}.md" if not ch_id.endswith(".md") else CH_DIR / ch_id
    p.write_text(md, encoding="utf-8")

def load_style():  return _read_json(STYLE_PATH, {})
def load_outline(): return _read_json(OUTLINE_PATH, {})
def load_memory():  return _read_json(MEM_PATH, {})
def save_memory(mem: dict): _write_json(MEM_PATH, mem)

def record_vote(ch_id: str, option_id: str, uid: str|None=None):
    rec = {"option_id": option_id, "uid": uid}
    p = VOTE_DIR / f"votes_{ch_id}.json"
    data = _read_json(p, {"records": []})
    data["records"].append(rec)
    _write_json(p, data)

def tally_votes(ch_id: str):
    p = VOTE_DIR / f"votes_{ch_id}.json"
    data = _read_json(p, {"records": []})
    tally = {}
    for r in data["records"]:
        tally[r["option_id"]] = tally.get(r["option_id"], 0) + 1
    return tally
