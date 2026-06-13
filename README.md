# NOVEL_SITE

AI Narrative Operating System（AI 長篇小說敘事系統）

## 專案簡介

NOVEL_SITE 是一套以長篇小說創作為核心的 AI 敘事系統。

專案目標並非單純使用 AI 產生小說，而是建立：

* 長篇記憶管理（Long-term Memory）
* 角色設定管理（Character Memory）
* 劇情大綱控制（Outline Control）
* 文風控制（Style Profile）
* 讀者投票互動（Interactive Story Branching）
* AI 與人類協作創作流程（Human-in-the-loop）

目前採用 Streamlit 作為前端介面。

---

## 專案現況（2026-06）

### 已完成

* Streamlit 多頁式介面
* 章節閱讀系統
* AI 續寫介面
* 角色記憶系統
* Style Profile 文風設定
* Summary 記憶摘要機制
* Chapter Outline 架構
* 投票系統基礎架構
* 草稿儲存機制

---

### 核心資料結構

```text
data/
├── chapters_md/
├── chapter_outlines.json
├── memory.json
├── style_profile.json
├── summaries.json
├── story_branch.json
├── story_decision.json
├── vote_config.json
└── vote_log.json
```

---

## 專案架構

```text
NOVEL_SITE
├── AI Generation
├── Memory Management
├── Outline Control
├── Style Profile
├── Reader Voting
├── Streamlit UI
└── Story Retrieval
```

---

## 主要檔案

### ai_chapter_generator.py

AI 自動生成章節核心。

### memory_manager.py

角色與世界觀記憶管理。

### batch_outline_builder.py

章節大綱生成與維護。

### summary_utils.py

摘要與前情提要管理。

### openai_helpers.py

模型呼叫封裝。

---

## Streamlit 頁面

```text
pages/
├── 00_章節閱讀.py
├── 01_生成新章節.py
├── 03_讀者投票結果.py
├── 04_讀者投票.py
└── 手機閱讀模式.py
```

---

## 啟動方式

建立虛擬環境：

```bash
python -m venv .venv
source .venv/bin/activate
```

安裝依賴：

```bash
pip install -r requirements.txt
```

啟動：

```bash
streamlit run app_demo.py
```

---

## 已知問題

目前為歷史專案整理階段。

已確認：

* 部分章節資料需重新整理
* OpenAI SDK 需更新驗證
* AI_CORE 整合尚未完成
* 投票系統尚未重新測試
* 自動生成流程尚未全面驗證

---

## Roadmap

### v1.2

* 三種生成模式整合
* 章節副標題
* 投票系統完善
* 草稿版本管理

### v1.3

* 個人化劇情分支
* 角色圖鑑
* SEO 優化

### v2.0

* 雲端部署
* 多使用者登入
* 自動通知系統

---

## 專案定位

本專案並非單純 AI 寫小說工具。

目標是建立：

「AI 長篇敘事作業系統（AI Narrative Operating System）」

透過多層記憶與人機協作機制，提升 AI 長篇創作的穩定性與一致性。
