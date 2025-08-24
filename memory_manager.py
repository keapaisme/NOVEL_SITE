# 功能：產生/合併角色記憶
# 指令：python memory_manager.py

import json
from pathlib import Path
from typing import Dict, Any


MEM_FILE = Path("ai_novel_tools/data/memory.json")

DEFAULT_MEMORY: Dict[str, Any] = {
    "schema_version": 1,
    "updated_by": "script:pack_and_reset.py",
    "characters": {},
    "events": [],
    "plot_flags": {}
}
,
            "notes": [
                "潛意識仍記得前世戀情（對象為賀雨蘭 HYL）",
                "英文常見寫成 YHL（排版美學：H 在上，HL 在下，呈金字塔型）"
            ]
        },
        "LCF": {
            "name": "林初妃",
            "aliases": ["A", "LCF"],
            "role": "女主",
            "tags": ["特助", "秘書", "貴氣", "天蠍"],
            "traits": ["對 HYH 一往情深", "沉穩果決", "職場高效"],
            "relationships": {
                "HYH": "現任特助/女友傾向；照護其失憶",
                "HYL": "她前幾世即是 HYL（本人未知）"
            },
            "notes": ["前幾世為 HYL，本人尚未自覺"]
        },
        "HYL": {
            "name": "賀雨蘭",
            "aliases": ["B", "HYL", "YHL"],
            "role": "女二",
            "tags": ["前世戀人"],
            "traits": ["與 HYH 前世情緣深厚", "緣分多舛"],
            "relationships": {
                "HYH": "前世男女朋友",
                "LCF": "現世身份轉生關係（LCF 即前世 HYL）"
            },
            "notes": ["常被寫作 YHL（排版美學原因）"]
        }
    },
    "events": [],
    "plot_flags": {
        "HYH_amnesia": True,
        "LCF_is_HYL_past_life": True,
        "YHL_spelling_rule": "HYL 常寫作 YHL，金字塔排版說明：H 在上，HL 在下"
    },
    "spelling_rules": {
        "HYL": "可寫作 YHL；視覺呈現可採金字塔：頂層 H、底層 HL"
    }
}

def load_memory() -> Dict[str, Any]:
    if MEM_FILE.exists():
        try:
            return json.loads(MEM_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def save_memory(mem: Dict[str, Any]):
    MEM_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEM_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")

def ensure_defaults():
    current = load_memory()
    merged = deep_merge(current, DEFAULT_MEMORY)
    save_memory(merged)
    print(f"✅ memory.json updated at {MEM_FILE}")

if __name__ == "__main__":
    ensure_defaults()
