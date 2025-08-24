# batch_outline_builder.py (robust JSON + debug + per-file error isolation)
import os, json, re, sys
from pathlib import Path
from typing import Dict, Any
from openai_helpers import chat_once  # 確保 openai_helpers.py 可被 import

CHAPTER_DIR = Path("data/chapters_md")
OUT_DIR     = Path("data/outlines")
INDEX_JSON  = Path("data/chapter_outlines.json")
CACHE_JSON  = Path("data/cache/outlines_cache.json")
ERROR_LOG   = Path("data/cache/outlines_errors.log")

OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_JSON.parent.mkdir(parents=True, exist_ok=True)

DEBUG = os.getenv("OUTLINE_DEBUG", "0") == "1"

SYS = (
    "你是專業小說編輯，擅長將章節整理為綱要。\n"
    "務必只輸出有效 JSON，不得包含任何額外說明、文字或程式碼圍欄。"
)

PROMPT_TMPL = """請將以下章節內容整理為「章節綱要」，要求：
- 以繁體中文輸出
- 條列 4~8 點關鍵要點（短句）
- 列出出現的主要角色（保留人名）
- 捕捉關鍵事件、衝突、轉折
- 盡量避免劇透下一章內容

只輸出純 JSON，結構如下（注意：務必是有效 JSON）：
{{
  "title": "<檔名或章節標題>",
  "bullets": ["要點1", "要點2", "..."],
  "characters": ["角色A","角色B"],
  "places": ["地點A","地點B"],
  "timeline": ["關鍵時間/順序節點（可留空）"]
}}

章節文本（節選或全文）：
{content}
"""

def _loose_json_parse(text: str) -> Dict[str, Any]:
    """從模型回應中盡量抽出第一個 JSON 物件。"""
    if not text or not text.strip():
        raise ValueError("模型回應為空")
    # 去掉可能的 ``` 圍欄
    t = text.strip()
    t = re.sub(r"^```(?:json|JSON)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    # 抽第一個 {...}
    m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        raise ValueError("回應中找不到 JSON 物件")
    core = m.group(0).strip()
    return json.loads(core)

def outline_one(name: str, text: str) -> Dict[str, Any]:
    """對單一章節做綱要；回傳 dict。"""
    user_msg = PROMPT_TMPL.format(content=text[:7000])
    content = chat_once(
        messages=[
            {"role": "system", "content": SYS},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=800
    )
    if DEBUG:
        print(f"\n---[RAW {name} (first 800 chars)]---\n{(content or '')[:800]}\n---[END]---", file=sys.stderr)

    try:
        data = json.loads(content)
    except Exception:
        data = _loose_json_parse(content)

    # 補齊必要欄位，避免後續寫檔時 KeyError
    data.setdefault("title", name)
    data.setdefault("bullets", [])
    data.setdefault("characters", [])
    data.setdefault("places", [])
    data.setdefault("timeline", [])
    # 內容型別防呆
    for k in ("bullets", "characters", "places", "timeline"):
        if not isinstance(data.get(k), list):
            data[k] = []
    if not isinstance(data.get("title"), str):
        data["title"] = str(name)
    return data

def run():
    # 載入快取
    try:
        cache = json.loads(CACHE_JSON.read_text(encoding="utf-8")) if CACHE_JSON.exists() else {}
    except Exception:
        cache = {}

    if not CHAPTER_DIR.exists():
        raise SystemExit(f"❌ 找不到章節資料夾：{CHAPTER_DIR.resolve()}")
    files = sorted(CHAPTER_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"❌ {CHAPTER_DIR.resolve()} 中沒有 .md 章節檔")

    index = {}
    for p in files:
        key = p.name
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            if key in cache:
                data = cache[key]
            else:
                data = outline_one(key, text)
                cache[key] = data
                CACHE_JSON.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

            # 寫單章綱要 .md
            md_path = OUT_DIR / (p.stem + "_綱要.md")
            bullets = "\n".join([f"- {b}" for b in data.get("bullets", [])])
            md = (
                f"# {data.get('title', p.stem)} 綱要\n\n"
                f"{bullets}\n\n"
                f"**角色**：{', '.join(data.get('characters', []))}\n\n"
                f"**地點**：{', '.join(data.get('places', []))}\n"
            )
            md_path.write_text(md, encoding="utf-8")

            index[key] = data

        except Exception as e:
            # 記錄錯誤但不中斷
            ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
            with ERROR_LOG.open("a", encoding="utf-8") as f:
                f.write(f"[{key}] {type(e).__name__}: {e}\n")
            if DEBUG:
                print(f"⚠️ 綱要失敗：{key} → {e}", file=sys.stderr)
            # 也把空白條目塞進索引，避免缺洞
            index[key] = {
                "title": p.stem,
                "bullets": [],
                "characters": [],
                "places": [],
                "timeline": []
            }

    INDEX_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Outlines saved to {OUT_DIR}, index: {INDEX_JSON}")
    if ERROR_LOG.exists():
        print(f"ℹ️ 有錯誤已記錄：{ERROR_LOG}")

if __name__ == "__main__":
    run()