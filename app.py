# app.py
import os
from time import time
import uuid

import streamlit as st

from llm import LLM, summarize
from database import get_conversations, save_message, load_messages, load_messages_by_conversation_id, save_summary, get_summary


# 定数定義
DEFAULT_TITLE = "marcy's ChatBot"
USER_NAME = "user"
ASSISTANT_NAME = "assistant"
PROVIDER="OpenAI"
MODEL="gpt-3.5-turbo"
SYSTEM="必ず日本語で返答してください。"
MAX_TOKENS=2048

title = DEFAULT_TITLE
st.title(title)

# データベースから会話履歴を読み込み、session_stateに保存
if 'chat_log' not in st.session_state:
    st.session_state.chat_log = load_messages()

conversations = get_conversations()

# サイドバーに会話のボタンを表示
with st.sidebar:
    if st.button("新規会話", key="new"):
        # 新規会話のための一意なconversation_idを生成し、st.session_stateに保存
        st.session_state.selected_conversation_id = str(uuid.uuid4())
    with st.expander("History"):
        for conversation_id, timestamp in get_conversations():
            formatted_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            summary = get_summary(conversation_id)
            # st.write(f"{formatted_timestamp}")
            st.subheader(f"{formatted_timestamp}", divider='rainbow')
            if st.button(f"{summary}", key=conversation_id):
                st.session_state.selected_conversation_id = conversation_id

        # 新規会話の場合、IDを生成してセッションステートに保存
        if "new_conversation" not in st.session_state:
            st.session_state.new_conversation = True

with st.sidebar:
    user_openai_api_key = st.text_input(
        label="OpenAI API key",
        value=os.environ.get("OPENAI_API_KEY"),
        placeholder="Paste your OpenAI API key",
        type="password"
    )
    user_anthropic_api_key = st.text_input(
        label="Anthropic API key",
        value=os.environ.get("ANTHROPIC_API_KEY"),
        placeholder="Paste your Anthropic API key",
        type="password"
    )
    os.environ['OPENAI_API_KEY'] = user_openai_api_key
    os.environ['ANTHROPIC_API_KEY'] = user_anthropic_api_key
    select_provider = st.selectbox("Provider", ["OpenAI", "Anthropic"], index=1)
    PROVIDER = select_provider
    if PROVIDER == "OpenAI":
        select_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4-1106-preview"], index=0)
    else:
        select_model = st.selectbox("Model", ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"], index=0)
    MODEL = select_model
    MAX_TOKENS = st.select_slider("Max Tokens", options=[128, 256, 512, 1024, 2048, 4096], value=1024)
    select_temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.0, step=0.1,)
    # select_chunk_size = st.slider("Chunk", min_value=0.0, max_value=1000.0, value=300.0, step=10.0,)

llm = LLM(model_provider=PROVIDER, model_name=MODEL, temperature=select_temperature, system_message=SYSTEM)

# ボタンクリックに基づいて会話を処理
if 'selected_conversation_id' in st.session_state:
    conversation_id = st.session_state.selected_conversation_id

    if conversation_id == "new":
        # 新規会話のIDを生成
        conversation_id = str(uuid.uuid4())
        st.session_state.selected_conversation_id = conversation_id
        st.write("新規会話を開始します。メッセージを入力してください。")
        llm.reset_memory()  # メモリのリセット
    
    # 既存の会話が選択された場合、その会話のメッセージを表示
    else:
        selected_messages = load_messages_by_conversation_id(conversation_id)
        for chat in selected_messages:
            with st.chat_message(chat["sender"]):
                st.write(chat["message"])
                if chat["caption"] != "":
                    st.caption(chat["caption"])
        llm.load_messages_into_memory(selected_messages)  # 会話をメモリにロード

    if user_msg := st.chat_input("ここにメッセージを入力"):
        # 最新のメッセージを表示
        t0 = time()
        with st.chat_message(USER_NAME):
            st.write(user_msg)

        with st.chat_message(ASSISTANT_NAME):
            assistant_msg = ""
            assistant_response_area = st.empty()
            for chunk in llm.stream(user_msg):
                assistant_msg += chunk.content
                assistant_response_area.write(assistant_msg + "▌")
            assistant_response_area.write(assistant_msg)
            t = time()-t0
            caption = f"time: {t:.1f}s, model: {select_model}, memory: {llm.load_memory()}"
            st.caption(caption)

        # セッションにチャットログを追加
        st.session_state.chat_log.append({"sender": USER_NAME, "message": user_msg, "caption": ""})
        st.session_state.chat_log.append({"sender": ASSISTANT_NAME, "message": assistant_msg, "caption": caption})
        # st.write(st.session_state.chat_log)
        # conversation_id = st.session_state.get('selected_conversation_id', 'default')
        conversation_id = st.session_state.selected_conversation_id
        save_message(USER_NAME, user_msg, "", st.session_state.selected_conversation_id)
        save_message(ASSISTANT_NAME, assistant_msg, caption, st.session_state.selected_conversation_id)

        # 要約の生成と保存
        selected_messages = load_messages_by_conversation_id(conversation_id)
        llm.load_messages_into_memory(selected_messages)
        saved_summary = summarize(llm.load_memory())  # 会話内容から要約を生成
        save_summary(saved_summary, conversation_id)  # 正しいconversation_idを使用して要約を保存
        st.rerun()  # UIの更新

else:
    st.write("サイドバーから「新規会話」をクリックするか、「History」を開き、過去の会話を選択してください。")
