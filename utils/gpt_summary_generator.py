# 📅 生成時間：2025-08-22 23:58
# 🛠️ 功能說明：根據輸入章節內容，自動使用 GPT 模型生成 1～2 句摘要
# 🧾 用途：用於自動摘要、批量摘要流程（被 batch_summarize.py 呼叫）

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_summary(chapter_text: str, language: str = "zh") -> str:
    """
    根據輸入章節內容，自動生成精簡摘要。
    :param chapter_text: 章節全文
    :param language: 'zh'（預設）或 'en'
    :return: 章節摘要字串
    """
    prompt = (
        "請閱讀以下小說章節，並生成一段 1～2 句話的摘要，用以顯示給讀者：\n\n"
        f"{chapter_text}\n\n摘要："
    ) if language == "zh" else (
        "Please summarize the following chapter into 1-2 sentences for readers:\n\n"
        f"{chapter_text}\n\nSummary:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ 摘要產生失敗：{e}"
