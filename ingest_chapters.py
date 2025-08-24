from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Single OpenAI entrypoint
from openai_helpers import chat_once

DATA_DIR = Path("data")
CHAPTERS_DIR = DATA_DIR / "chapters_md"
STYLE_PROFILE_JSON = DATA_DIR / "style_profile.json"

SCHEMA_HINT = {
    "language": "Chinese",
    "genre": "Romantic Drama",
    "voice": "Third-person limited",
    "pov": "Third-person",
    "tense": "Past",
    "tone": "Emotional, Reflective",
    "pacing": "Moderate",
    "sentence_length": "Medium",
    "vocabulary": "Contemporary, Emotional",
    "idioms": [],
    "tropes": [],
    "themes": [],
    "formatting": "Standard narrative with chapter headings",
    "do": [],
    "dont": [],
    "recurring_characters": [],
    "world_facts": [],
    "content_guidelines": [],
    "avoid": [],
    "sample_signature": ""
}

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Try to parse JSON from the model output. Handles fenced code blocks and trailing text.
    """
    # Fenced ```json ... ``` or ``` ... ```
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence:
        text = fence.group(1)
    # First {...} block
    m = re.search(r"(\{[\s\S]*\})", text)
    if m:
        text = m.group(1)
    return json.loads(text)

def build_style_profile(samples: List[str], model: str = "gpt-4o") -> Dict[str, Any]:
    """
    Analyze given text samples and produce a JSON style card for downstream generators.
    Output schema matches STYLE_PROFILE_JSON.
    """
    joined = "\n\n--- SAMPLE SPLIT ---\n\n".join(s[:4000] for s in samples if s.strip())
    user_prompt = f"""
你是小說總編。請嚴格輸出「單一 JSON 物件」，用繁體中文，欄位需與下列 SCHEMA 完全一致並可被程式直接使用。
目的：供 AI 生成後續章節時維持統一文風。

SCHEMA（鍵名不可更改）：
{json.dumps(SCHEMA_HINT, ensure_ascii=False, indent=2)}

要求：
- language 固定 "Chinese"
- idioms / tropes / themes / do / dont / content_guidelines / avoid：輸出具體條目陣列
- recurring_characters / world_facts：若能從樣本文字推斷，請列出
- sample_signature：擷取能代表此文風的 1~2 句示例（勿超過 120 字）
- 僅輸出 JSON，不得出現解說文字

供分析的樣本片段：
{joined}
""".strip()

    resp = chat_once(
        messages=[{"role": "user", "content": user_prompt}],
        model=model,
        temperature=0.3,
        max_tokens=1200,
    )
    content = getattr(resp, "choices", [None])[0].message.content if hasattr(resp, "choices") else resp
    data = _extract_json(content)
    # fill minimal defaults and normalize keys
    final = {**SCHEMA_HINT, **data}
    # Ensure types
    for k in ["idioms", "tropes", "themes", "do", "dont", "recurring_characters", "world_facts", "content_guidelines", "avoid"]:
        if not isinstance(final.get(k), list):
            final[k] = []
    for k in ["language","genre","voice","pov","tense","tone","pacing","sentence_length","vocabulary","formatting","sample_signature"]:
        final[k] = str(final.get(k, SCHEMA_HINT.get(k, "")))
    return final

def collect_samples(max_files: int = 12) -> List[str]:
    """
    Select a small, diverse set of chapter files as analysis samples.
    Strategy: earliest few + every 5th + latest few.
    """
    if not CHAPTERS_DIR.exists():
        return []
    files = sorted(CHAPTERS_DIR.glob("*.md"))
    if not files:
        return []
    picks = []
    # earliest 3
    picks += files[:3]
    # every 5th
    picks += [p for idx, p in enumerate(files, start=1) if idx % 5 == 0]
    # latest 3
    picks += files[-3:]
    # de-dup and cap
    seen = set()
    uniq = []
    for p in picks:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    uniq = uniq[:max_files]
    return [p.read_text(encoding="utf-8") for p in uniq]

def save_style_profile(profile: Dict[str, Any]) -> None:
    STYLE_PROFILE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STYLE_PROFILE_JSON.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已輸出風格卡：{STYLE_PROFILE_JSON}")

def main():
    samples = collect_samples()
    if not samples:
        print("⚠️ 找不到樣本：請先放入 data/chapters_md/*.md")
        return
    profile = build_style_profile(samples)
    save_style_profile(profile)

if __name__ == "__main__":
    main()