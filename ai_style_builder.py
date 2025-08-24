# ai_style_builder.py  (robust / tolerant JSON parsing)
import os, re, json, sys
from pathlib import Path
from typing import List, Dict
from openai_helpers import chat_once  # 與同層或 PYTHONPATH 可被 import
# 若 import 失敗，請把 openai_helpers.py 放到同資料夾，或在執行時加 PYTHONPATH

CHAPTER_DIR = Path("data/chapters_md")
OUTPUT_FILE = Path("data/style_profile.json")
DEBUG = os.getenv("STYLE_DEBUG", "0") == "1"

def load_chapters(limit_chars_per_file: int = 8000) -> List[Dict]:
    if not CHAPTER_DIR.exists():
        raise SystemExit(f"❌ 找不到章節資料夾：{CHAPTER_DIR.resolve()}")
    files = sorted([p for p in CHAPTER_DIR.glob("*.md")])
    if not files:
        raise SystemExit(f"❌ {CHAPTER_DIR.resolve()} 中沒有 .md 章節檔")
    chapters = []
    for p in files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        # 去掉「本章摘要」區，避免影響風格分析
        txt = re.split(r"\n-{3,}\n\s*📘\s*本章摘要[:：]", txt, maxsplit=1)[0]
        chapters.append({"filename": p.name, "text": txt[:limit_chars_per_file]})
    if DEBUG:
        print(f"✅ 已載入章節數：{len(chapters)}", file=sys.stderr)
    return chapters

STYLE_SYS = (
    "你是專業小說風格分析師，擅長從文本中萃取可操作的寫作風格說明。"
    "務必只輸出有效 JSON，不得有任何多餘文字。"
)

STYLE_USER_TMPL = """請根據多個章節文本，產出『風格手冊 JSON』。
只輸出**純 JSON**，不得包含任何說明、註解、程式碼圍欄(如 ```json )、前後標記。
若無法取得某欄位，請給空字串或空陣列。

需求：
- 以輸入文本的平均風格為主，不要誤入章節內角色語氣
- 給出可操作的「寫作規則」與「避免清單」
- 補充 100~150 字的 style sample 以示範筆調

輸出 JSON key：
language, genre, voice, pov, tense, tone, pacing, sentence_length,
vocabulary, idioms, tropes, themes, formatting, do, dont,
recurring_characters, world_facts, content_guidelines, avoid, sample_signature

文本摘錄（可能節選）：
{payload}
"""

def _loose_json_parse(text: str) -> dict:
    """盡量從模型回應中抽到 JSON：去掉 ``` 區塊、抓最外層 {...}。"""
    if not text or not text.strip():
        raise ValueError("模型回應為空")
    # 去掉可能的 code fences
    text = re.sub(r"^```[\s\S]*?\n", "", text.strip())      # 頭部 ```lang
    text = re.sub(r"\n```$", "", text.strip())              # 尾部 ```
    # 抽取第一個 { ... } 區塊（貪婪到最後一個右大括號）
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("回應中找不到 JSON 物件")
    core = m.group(0).strip()
    return json.loads(core)

def build_style_profile():
    chapters = load_chapters()
    # 串 payload：每篇取一小段，控制 token
    parts = []
    for ch in chapters:
        sample = ch["text"][:1200]
        first_line = ch["text"].splitlines()[0] if ch["text"] else ch["filename"]
        parts.append(f"《{ch['filename']}》\n{sample}\n")
    payload = "\n\n".join(parts)[:24000]

    content = chat_once(
        messages=[
            {"role": "system", "content": STYLE_SYS},
            {"role": "user", "content": STYLE_USER_TMPL.format(payload=payload)}
        ],
        # 可用環境變數 OPENAI_MODEL 切換（預設 gpt-4o）
        temperature=0.2,
        max_tokens=1400
    )

    if DEBUG:
        print("\n---[RAW MODEL OUTPUT (first 800 chars)]---\n", content[:800], "\n---[END]---", file=sys.stderr)

    # 先直讀；失敗就用鬆弛解析
    try:
        style = json.loads(content)
    except Exception:
        style = _loose_json_parse(content)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(style, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ style_profile 已輸出：{OUTPUT_FILE.resolve()}")

if __name__ == "__main__":
    out = build_style_profile()