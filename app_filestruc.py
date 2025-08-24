import os
import streamlit as st

# 設定頁面標題
st.set_page_config(page_title="Novel Site", page_icon="📚", layout="wide")
st.title("Novel Site 後台")

# 設定章節所在的資料夾
CHAPTER_FOLDER = "data/chapters_md"  # 假設你的 .md 檔都在這個資料夾中

# 取得所有 .md 檔案清單（排序）
chapter_files = sorted([f for f in os.listdir(CHAPTER_FOLDER) if f.endswith(".md")])

# 建立章節選單（從檔名中去掉 .md）
chapter_titles = [f.replace(".md", "") for f in chapter_files]

# 顯示選單
selected_title = st.selectbox("📖 選擇章節", chapter_titles)

# 讀取對應的 md 檔案內容
selected_file_path = os.path.join(CHAPTER_FOLDER, selected_title + ".md")
with open(selected_file_path, "r", encoding="utf-8") as f:
    chapter_content = f.read()

# 顯示內容
st.markdown(f"# {selected_title}")
st.markdown(chapter_content)
