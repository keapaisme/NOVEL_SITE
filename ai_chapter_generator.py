import os, json
from pathlib import Path
from datetime import datetime
from openai_helpers import chat_once

CHAPTER_DIR = Path("data/chapters_md")
STYLE_FILE  = Path("data/style_profile.json")
MEM_FILE    = Path("ai_novel_tools/data/memory.json")
OUTLINE_IDX = Path("data/chapter_outlines.json")  # optional

def load_json(p: Path):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

SYS = "你是專精於霸總言情的小說寫作助手，擅長延續固定筆調、維護角色設定與長線伏筆。"

GEN_TMPL = """【寫作風格手冊（節選）】
{style}

【世界觀與角色記憶（節選）】
{memory}

【前情綱要（可選）】
{outline_hint}

【任務】
- 以上述「風格」與「角色記憶」延續小說，寫出新一章
- 使用繁體中文，維持既有人物口吻、敘事視角與時態
- 目標字數（可浮動）：{target_words} 字左右
- 本章的副標題：{subtitle}
- 章節內避免總結語，留出懸念

【輸出格式】
直接輸出章節正文，不要再加任何額外標題或說明。
"""

def next_chapter_number():
    CHAPTER_DIR.mkdir(parents=True, exist_ok=True)
    count = len(list(CHAPTER_DIR.glob("*.md")))
    return count + 1

def generate(subtitle: str, target_words: int = 1200):
    style = load_json(STYLE_FILE)
    memory = load_json(MEM_FILE)
    outlines = load_json(OUTLINE_IDX)

    outline_hint = ""
    if outlines:
        last = sorted(outlines.keys())[-1]
        import json as _json
        outline_hint = _json.dumps(outlines[last], ensure_ascii=False)

    content = chat_once(
        messages=[
            {"role": "system", "content": SYS},
            {"role": "user", "content": GEN_TMPL.format(
                style=json.dumps(style, ensure_ascii=False)[:4000] or "(尚未建立)",
                memory=json.dumps(memory, ensure_ascii=False)[:4000] or "(尚未建立)",
                outline_hint=outline_hint[:2000],
                target_words=target_words,
                subtitle=subtitle or "未命名"
            )}
        ],
        temperature=0.9, max_tokens=2500
    )

    n = next_chapter_number()
    today = datetime.now().strftime("%Y-%m-%d")
    safe = "".join(c for c in subtitle if c.isalnum() or c in (" ", "_", "-")).rstrip() or "未命名"
    filename = f"{today}_第{n}章_{safe}.md"
    path = CHAPTER_DIR / filename
    md = f"# 第{n}章 {subtitle or '未命名'}\n\n{content}\n\n---\n\n📘 本章摘要：\n（生成後可用 summary_utils 另行補上）\n"
    path.write_text(md, encoding="utf-8")
    print(f"✅ New chapter saved: {path}")
    return path

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--subtitle", required=True, help="本章副標題")
    ap.add_argument("--words", type=int, default=1200, help="目標字數")
    args = ap.parse_args()
    generate(args.subtitle, args.words)
