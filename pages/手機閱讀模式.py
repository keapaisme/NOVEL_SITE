import streamlit as st
import os

st.title("章節閱讀 - 簡潔版")

CHAPTER_FOLDER = "data/chapters_md"
chapter_files = sorted([f for f in os.listdir(CHAPTER_FOLDER) if f.endswith(".md")])
chapter_titles = [f.replace(".md", "") for f in chapter_files]

selected_title = st.selectbox("選擇章節", chapter_titles)
selected_file_path = os.path.join(CHAPTER_FOLDER, selected_title + ".md")

if os.path.exists(selected_file_path):
    with open(selected_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if lines and lines[0].startswith("#"):
        title_line = lines[0].lstrip("#").strip()
        body = "".join(lines[1:])
        st.markdown(f"## {title_line}")
        st.markdown("---")
        st.markdown(body)
    else:
        st.markdown("".join(lines))
else:
    st.warning("找不到章節檔案")
