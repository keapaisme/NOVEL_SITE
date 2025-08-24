import os
from dotenv import load_dotenv
from openai import OpenAI, BadRequestError

load_dotenv()

def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

def _msgs_to_text(messages):
    # 將 messages 攤平為單一文字，給 Responses API 用
    parts = []
    for m in messages:
        role = m.get("role", "user").upper()
        parts.append(f"{role}: {m.get('content','')}")
    return "\n\n".join(parts)

def chat_once(messages, model=None, temperature=0.7, max_tokens=2000):
    model = model or os.getenv("OPENAI_MODEL") or "gpt-4o"
    client = _get_client()

    # 1) 先試 Chat Completions（max_tokens）
    try:
        r = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return r.choices[0].message.content
    except BadRequestError as e:
        emsg = str(e)
        # 2) 不支援 max_tokens → 用 Responses API（input + max_output_tokens）
        if ("max_tokens" in emsg and "supported" in emsg) or "use max_completion_tokens" in emsg:
            txt = _msgs_to_text(messages)
            r = client.responses.create(
                model=model,
                input=txt,
                temperature=temperature,
                max_output_tokens=max_tokens,  # 關鍵：這裡不是 max_tokens
            )
            # 取文本
            try:
                return r.output_text
            except Exception:
                try:
                    # 兼容早期結構
                    return r.output[0].content[0].text
                except Exception:
                    return str(r)
        # 其他錯照拋
        raise
    except Exception as e:
        raise RuntimeError(f"OpenAI error: {type(e).__name__}: {e}")
