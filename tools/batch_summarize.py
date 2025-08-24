# 📅 重構時間：2025-08-23 00:05
# 🛠️ 功能說明：批量摘要章節為 summaries.json，可切換 local 或 GPT 模式，避免重複處理
# 🧾 用途：提供投票模組、搜尋引擎、章節記憶等共用摘要資料來源

import os, json, argparse, hashlib, time
from datetime import datetime
from pathlib import Path

from utils import gpt_summary_generator  # ✅ 改用你整合好的 GPT 模組

CHAPTER_DIR = Path("data/chapters_md")
OUT_PATH = Path("data/summaries.json")

PROMPT = ("請閱讀以下章節內容，產生精煉摘要(80-120字)、列出3-6個關鍵字，並盡量推測主要角色名單。"
          "以JSON輸出: {summary: string, keywords: string[], characters: string[]}")

def md5_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_cache(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            return {}
    return {}

def save_cache(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def local_summarize(md_text: str) -> dict:
    lines = [ln.strip() for ln in md_text.splitlines() if ln.strip()]
    title = lines[0].lstrip("# ") if lines and lines[0].startswith("#") else "(無標題)"
    body = next((ln for ln in lines[1:] if not ln.startswith("#")), "")
    summary = (body[:120] + "…") if len(body) > 120 else body
    kw = [k for k in ["愛", "回憶", "公司", "祕密", "重逢"] if k in md_text]
    chars = [n for n in ["林初妃", "賀宇珩", "小毅", "總監"] if n in md_text]
    return {"summary": summary or title, "keywords": kw[:6], "characters": chars[:6]}

def api_summarize(md_text: str, model: str = "gpt-4o") -> dict:
    try:
        result = gpt_summary_generator.generate_summary(md_text)
        return {"summary": result, "keywords": [], "characters": []}  # 若 GPT 模型支援可改進
    except Exception as e:
        return {"summary": f"⚠️ GPT 摘要失敗：{e}", "keywords": [], "characters": []}

def main():
    ap = argparse.ArgumentParser(description="Batch summarize chapters → summaries.json")
    ap.add_argument("--dir", default=str(CHAPTER_DIR), help="章節資料夾")
    ap.add_argument("--out", default=str(OUT_PATH), help="輸出 summaries.json 路徑")
    ap.add_argument("--mode", choices=["local", "api"], default="local", help="摘要模式")
    ap.add_argument("--only-missing", action="store_true", help="僅產生缺少或變動的章節")
    args = ap.parse_args()

    chapter_dir = Path(args.dir)
    out_path = Path(args.out)

    cache = load_cache(out_path)
    if not isinstance(cache, dict):
        cache = {}

    files = sorted([p for p in chapter_dir.glob("*.md")])
    updated = 0

    for p in files:
        md_text = p.read_text("utf-8")
        digest = md5_text(md_text)
        entry = cache.get(p.name)
        if args.only_missing and entry and entry.get("hash") == digest:
            continue

        data = local_summarize(md_text) if args.mode == "local" else api_summarize(md_text)
        now = datetime.now().isoformat(timespec="seconds")
        cache[p.name] = {
            "hash": digest,
            "title": md_text.splitlines()[0].lstrip("# ") if md_text.startswith("#") else p.stem,
            "summary": data.get("summary", ""),
            "keywords": data.get("keywords", []),
            "characters": data.get("characters", []),
            "updated_at": now,
        }
        updated += 1
        print(f"[OK] {p.name}")
        time.sleep(0.2)

    save_cache(out_path, cache)
    print(f"Done. {updated} file(s) updated → {out_path}")

if __name__ == "__main__":
    main()
