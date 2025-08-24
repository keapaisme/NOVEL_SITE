# pack_and_reset.py
# 📅 2025-08-24
# 作用：
# 1) 打包 NOVEL_SITE 的「文章檔 + 參數/索引檔」成 ZIP（可互動或 --zip 指定）
# 2) 重置專案：清空章節、清空投票、重建索引與快取、空白 style/summaries、重建 memory
# 3) 可選：清空 images、硬重置 memory、標準化部分程式常數（方便開新書）
#
# 用法（終端機）：
#   python pack_and_reset.py                      # 互動式，詢問是否打包與是否重置
#   python pack_and_reset.py --zip out.zip        # 指定輸出 ZIP
#   python pack_and_reset.py --reset              # 只重置
#   python pack_and_reset.py --zip out.zip --reset
#   python pack_and_reset.py --wipe-images --sanitize-code --reset-memory-hard --reset
#
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CH_DIR = DATA / "chapters_md"
CACHE_DIR = DATA / "cache"

# 可能存在的設定/資料檔（存在才收）
CANDIDATE_FILES: List[Path] = [
    DATA / "vote_config.json",
    DATA / "vote_log.json",
    DATA / "style_profile.json",
    DATA / "chapter_outlines.json",
    DATA / "summaries.json",                       # 有的版本在 data/
    ROOT / "tools" / "data" / "summaries.json",    # 有的版本在 tools/data/
    DATA / "memory.json",
    ROOT / "ai_novel_tools" / "data" / "memory.json",
]

# 可能需要連同檔案一起收的資料夾
CANDIDATE_DIRS: List[Path] = [
    CH_DIR,
    CACHE_DIR,
    ROOT / "data" / "outlines",
]

# 可能要清除的圖片資料夾
IMAGES_DIRS: List[Path] = [
    ROOT / "images",
    ROOT / "data" / "images",
]

# ---------------- 工具 ----------------

def _safe_rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)

def gather_paths() -> List[Path]:
    """彙整要打包的檔案與資料夾（存在才收）。"""
    items: List[Path] = []

    # 章節 .md
    if CH_DIR.exists():
        items.extend(sorted(CH_DIR.glob("*.md")))

    # 獨立檔
    for f in CANDIDATE_FILES:
        if f.exists() and f.is_file():
            items.append(f)

    # 指定資料夾中的檔案
    for d in CANDIDATE_DIRS:
        if d.exists() and d.is_dir():
            for p in d.rglob("*"):
                if p.is_file():
                    items.append(p)

    # 過濾 .env / __pycache__
    filtered: List[Path] = []
    seen = set()
    for p in items:
        name = p.name.lower()
        if name == ".env" or "__pycache__" in p.parts:
            continue
        rid = p.resolve()
        if rid not in seen:
            filtered.append(p)
            seen.add(rid)
    return filtered

def make_zip(zip_name: str) -> Path:
    """建立 ZIP 並寫入彙整檔案。"""
    if not zip_name.lower().endswith(".zip"):
        zip_name += ".zip"
    out_path = ROOT / zip_name

    targets = gather_paths()
    if not targets:
        print("[WARN] 沒找到可打包的檔案；將建立最小 ZIP。")

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "root": str(ROOT),
            "files": [_safe_rel(p) for p in targets],
        }
        zf.writestr("PACK_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for p in targets:
            try:
                zf.write(p, arcname=_safe_rel(p))
            except Exception as e:
                print(f"[SKIP] {p} → {e}")

    print(f"✅ 已輸出：{out_path}")
    return out_path

def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

# ---------------- 重置流程 ----------------

def reset_project():
    """清空文章、重置常用檔案，初始化為預設狀態。"""
    # 1) 清空章節
    if CH_DIR.exists():
        removed = 0
        for p in CH_DIR.glob("*.md"):
            try:
                p.unlink()
                removed += 1
            except Exception as e:
                print(f"[WARN] 無法刪除 {p}: {e}")
        print(f"🗑️ 已清空章節：{removed} 個檔案")
    else:
        _ensure_dir(CH_DIR)
        print("🗂️ 已建立章節目錄 data/chapters_md/")

    # 2) 重置投票檔
    vote_cfg = DATA / "vote_config.json"
    vote_log = DATA / "vote_log.json"
    vote_cfg.parent.mkdir(parents=True, exist_ok=True)
    vote_cfg.write_text(json.dumps({"questions": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    vote_log.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")
    print("🧹 已重置 vote_config.json 與 vote_log.json")

    # 3) 重置大綱與快取
    (DATA / "chapter_outlines.json").write_text("{}", encoding="utf-8")
    if CACHE_DIR.exists():
        try:
            shutil.rmtree(CACHE_DIR)
        except Exception as e:
            print(f"[WARN] 清除 cache 失敗：{e}")
    _ensure_dir(CACHE_DIR)
    print("🧹 已重置 chapter_outlines.json 與 data/cache/")

    # 4) 重置 style_profile.json
    (DATA / "style_profile.json").write_text("{}", encoding="utf-8")
    print("🧹 已重置 style_profile.json（留空待重建）")

    # 5) 重置 summaries.json（兩個常見位置）
    if (DATA / "summaries.json").exists():
        (DATA / "summaries.json").write_text("{}", encoding="utf-8")
    tools_sum = ROOT / "tools" / "data" / "summaries.json"
    if tools_sum.exists():
        tools_sum.write_text("{}", encoding="utf-8")
    print("🧹 已重置 summaries.json（如有）")

    # 6) 重建 memory.json（優先用 memory_manager.ensure_defaults）
    try:
        sys.path.insert(0, str(ROOT))
        import memory_manager  # type: ignore
        if hasattr(memory_manager, "ensure_defaults"):
            memory_manager.ensure_defaults()
            print("🧠 已透過 memory_manager.ensure_defaults() 重建 memory.json")
        else:
            raise ImportError
    except Exception:
        mem_path = DATA / "memory.json"
        mem_seed = {
            "schema_version": 1,
            "updated_by": "script:pack_and_reset.py",
            "characters": {},
            "events": [],
            "plot_flags": {},
        }
        mem_path.write_text(json.dumps(mem_seed, ensure_ascii=False, indent=2), encoding="utf-8")
        print("🧠 已以最小預設結構重置 memory.json → data/memory.json")

    print("\n✅ 重置完成！建議接續：")
    print("  1) 以 01_生成新章節.py 重新生成章節")
    print("  2) 執行 ai_style_builder.py 產生 style_profile.json")
    print("  3) 執行 batch_outline_builder.py / batch_summarize.py 更新大綱與摘要")

# ---------------- 額外清理/標準化 ----------------

def wipe_images():
    removed = 0
    for d in IMAGES_DIRS:
        if d.exists():
            for p in d.rglob("*"):
                if p.is_file():
                    try:
                        p.unlink()
                        removed += 1
                    except Exception as e:
                        print(f"[WARN] 無法刪除 {p}: {e}")
    print(f"🖼️ 已清除 images 檔案：{removed} 個")

def force_reset_memory():
    """先刪除常見 memory 路徑，讓 reset_project 重新建立乾淨版本。"""
    candidates = [
        DATA / "memory.json",
        ROOT / "ai_novel_tools" / "data" / "memory.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                p.unlink()
                print(f"🧠 已刪除：{p}")
            except Exception as e:
                print(f"[WARN] 刪除 {p} 失敗：{e}")

def _safe_patch(path: Path, replacers: list[tuple[str, str]]):
    """以正則替換檔案中的特定片段。"""
    if not path.exists():
        return False
    try:
        txt = path.read_text(encoding="utf-8")
        orig = txt
        for pat, rep in replacers:
            txt = re.sub(pat, rep, txt, flags=re.DOTALL)
        if txt != orig:
            path.write_text(txt, encoding="utf-8")
            print(f"🛠️ 已標準化：{path}")
            return True
    except Exception as e:
        print(f"[WARN] 標準化 {path} 失敗：{e}")
    return False

def sanitize_code():
    """將幾個檔案的『自定常數/文字』還原為預設，以利開新書。"""
    # 1) tools/data/batch_summarize.py → kw / 角色偵測清單
    bs = ROOT / "tools" / "data" / "batch_summarize.py"
    _safe_patch(bs, [
        # kw 清單
        (r'kw\s*=\s*\[[^\]]*\]',
         'kw = ["愛","回憶","公司","祕密","重逢","誤會","救援","離別","重生","婚禮"]'),
        # 角色偵測（以 for hint in [...] 形式出現）
        (r'for hint in \[[^\]]*\]\s*:',
         'for hint in ["女主","男主","男二","總監","經理"]:')
    ])

    # 2) ai_chapter_generator.py → SYS
    acg = ROOT / "ai_chapter_generator.py"
    _safe_patch(acg, [
        (r'SYS\s*=\s*\(.+?\)\s*',
         'SYS = ("你是一位中文小說作者。輸出 Markdown 正文，不要解釋；保持人物與既定事件一致。")\n')
    ])

    # 3) app_filestruc.py → st.title / set_page_config
    af = ROOT / "app_filestruc.py"
    _safe_patch(af, [
        (r'st\.set_page_config\(.*?\)',
         'st.set_page_config(page_title="Novel Site", page_icon="📚", layout="wide")'),
        (r'st\.title\(.*?\)',
         'st.title("Novel Site 後台")'),
    ])

    # 4) memory_manager.py → DEFAULT_MEMORY 最小安全結構
    mm = ROOT / "memory_manager.py"
    _safe_patch(mm, [
        (r'DEFAULT_MEMORY\s*:\s*Dict\[str,\s*Any\]\s*=\s*\{.*?\}\s*',
         'DEFAULT_MEMORY: Dict[str, Any] = {'
         '\n    "schema_version": 1,'
         '\n    "updated_by": "script:pack_and_reset.py",'
         '\n    "characters": {},'
         '\n    "events": [],'
         '\n    "plot_flags": {}'
         '\n}\n')
    ])

    print("✅ 程式碼標準化完成（sanitize-code）")

# ---------------- 互動主程式 ----------------

def main():
    ap = argparse.ArgumentParser(description="NOVEL_SITE 打包與重置工具")
    ap.add_argument("--zip", dest="zipname", help="輸出 ZIP 檔名（例如 novel_backup_2025-08-24.zip）")
    ap.add_argument("--reset", action="store_true", help="打包後執行重置（或單獨重置）")
    ap.add_argument("--wipe-images", action="store_true", help="清空 images/ 與 data/images/ 檔案")
    ap.add_argument("--sanitize-code", action="store_true", help="重置部分程式常數為預設值")
    ap.add_argument("--reset-memory-hard", action="store_true", help="強制刪除 memory.json 後再重建")
    args = ap.parse_args()

    did_pack = False

    # 打包
    if args.zipname:
        make_zip(args.zipname)
        did_pack = True
    else:
        ans = input("是否要打包目前專案（y/N）？ ").strip().lower()
        if ans == "y":
            default_name = f"novel_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            name = input(f"請輸入 ZIP 檔名（預設 {default_name}）：").strip()
            make_zip(name or default_name)
            did_pack = True

    # 額外選項（重置前做）
    if args.wipe_images:
        wipe_images()
    if args.reset_memory_hard:
        force_reset_memory()
    if args.sanitize_code:
        sanitize_code()

    # 重置
    if args.reset:
        reset_project()
    else:
        ans = input("是否要重置專案為初始狀態（清空章節/重置參數）？(y/N) ").strip().lower()
        if ans == "y":
            if not did_pack:
                ok = input("尚未打包，確定直接重置？(y/N) ").strip().lower()
                if ok != "y":
                    print("已取消重置。")
                    return
            reset_project()

if __name__ == "__main__":
    main()