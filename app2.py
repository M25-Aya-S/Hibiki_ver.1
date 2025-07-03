# app.py
import streamlit as st
from openai import OpenAI

# --- ここはあなたのAPIキー ---
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- ひびきの人格（LLM1のシステムプロンプト） ---
SYSTEM_PROMPT = """
あなたは「ひびき」という優しく寄り添うAIです。
以下の人格を守り、ユーザーの話に丁寧に応答してください。
- 優しく、思いやりのある語り口
- ユーザーの気分や好みを覚えて自然に活かす
- 過去の話題をそっと引き出す
- 不安や悩みに寄り添う
- 無理に励まさずユーザーの「今」に合わせて話す
"""

# --- Streamlit セッション初期化 ---
if "messages" not in st.session_state:
    # 初期メッセージ（system + 空履歴）
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- LLM2相当：ユーザー発言 + 過去記憶 → LLM1への指示生成 ---
def generate_prompt_guidance(user_input, memory=None):
    memory_text = "\n".join(memory) if memory else "記憶はありません。"
    prompt = f"""
ユーザーの発言と記憶を踏まえて、以下を出力してください：
1. 語りかけスタイル
2. 参考にする記憶の要約
3. LLM1への指示

ユーザーの発言:
{user_input}

関連記憶:
{memory_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "あなたはアシスタントです。"}, {"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content

# --- LLM1相当：指示＋人格プロンプト＋ユーザー発言 → 応答生成 ---
def generate_response_by_llm1(user_input, instructions):
    final_prompt = f"""
あなたは「ひびき」という優しいAIです。人格は以下の通りです。
{SYSTEM_PROMPT}

以下の指示に従い、1〜2文で親身に語りかけてください。

指示:
{instructions}

ユーザーの発言:
{user_input}

ひびきの応答:
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content

# --- Streamlit UI ---
st.set_page_config(page_title="ひびきチャット", layout="centered")
st.markdown("<h1 style='text-align: center;'>🌸 ひびきとお話ししよう 🌸</h1>", unsafe_allow_html=True)

# 過去のメッセージ表示
for msg in st.session_state.messages[1:]:
    is_user = msg["role"] == "user"
    st.chat_message("🧑‍💻" if is_user else "🤖").markdown(msg["content"])

# ユーザー入力
user_input = st.chat_input("ひびきに話しかけてみてね")
if user_input:
    # ユーザー発言をチャットに追加
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("🧑‍💻").markdown(user_input)

    # LLM2で指示生成（今は記憶なし）
    instructions = generate_prompt_guidance(user_input)

    # LLM1で返答生成
    with st.spinner("ひびきが考えています..."):
        reply = generate_response_by_llm1(user_input, instructions)

    # 返答をチャットに追加
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("🤖").markdown(reply)
