# app.py
import os
from time import time
import uuid
import yaml
import streamlit as st
from pydantic import ValidationError

from llm import LLM, summarize
from database import get_conversations, save_message, load_messages_by_conversation_id, save_summary, get_summary, delete_conversation, get_user, get_user_id, save_user, authenticate_user
from config import *


def main():
    # セッションステートの初期化
    initialize_session_state()

    if st.session_state.logged_in:
        # タイトルの設定
        st.title(DEFAULT_TITLE)

        # APIキーとモデル選択の設定
        setup_sidebar()

        if ((st.session_state.provider == "OpenAI" and not st.session_state.openai_api_key) 
            or (st.session_state.provider == "Anthropic" and not st.session_state.anthropic_api_key)):
            st.error("APIキーが設定されていません。サイドバーでAPIキーを入力してください。")
        else:
            # LLMのインスタンス化
            llm = LLM(
                model_provider=st.session_state.provider, 
                model_name=st.session_state.model, 
                system_message=SYSTEM, 
                openai_api_key=st.session_state.openai_api_key,
                anthropic_api_key=st.session_state.anthropic_api_key
            )
            # メインの処理
            conversation_id = st.session_state.get('selected_conversation_id', 'default')
            if conversation_id != 'default':
                process_conversation(conversation_id, llm)
            else:
                st.write("""サイドバーから"New Chat"をクリックするか、"History"を開き、過去の会話を選択してください。""")
    
    else:
        login()


def load_model_config():
    """model.yamlからモデル設定を読み込む"""
    try:
        with open('models.yaml', 'r') as file:
            config = yaml.safe_load(file)
            return config
    except FileNotFoundError:
        st.error("models.yamlファイルが見つかりません。")
        return None

def create_provider_and_model_lists(models_config):
    """プロバイダリストとモデルのリストを作成する"""
    if models_config is None:
        return [], []

    providers = list(models_config.keys())
    model_list = {provider: models for provider, models in models_config.items()}

    return providers, model_list

def handle_new_conversation():
    """新規会話の処理"""
    conversation_id = str(uuid.uuid4())
    st.session_state.selected_conversation_id = conversation_id
    st.write("新規会話を開始します。メッセージを入力してください。")
    return conversation_id

def handle_existing_conversation(conversation_id, llm):
    """既存の会話の処理"""
    selected_messages = load_messages_by_conversation_id(conversation_id)
    display_conversation(selected_messages)
    llm.load_messages_into_memory(selected_messages)
    return selected_messages

def display_conversation(messages):
    """会話の表示"""
    for message in messages:
        with st.container():
            with st.chat_message(message['sender']):
                st.write(f"{message['message']}")
                if message["caption"]:
                    st.caption(message["caption"])

def process_user_input(user_input, llm):
    """ユーザー入力の処理とLLMの応答取得"""
    start_time = time()
    with st.chat_message(USER_NAME):
        st.write(user_input)
    with st.chat_message(ASSISTANT_NAME):
        assistant_msg = ""
        assistant_response_area = st.empty()
        for chunk in llm.stream(user_input):
            assistant_msg += chunk.content
            assistant_response_area.write(assistant_msg + "▌")
        assistant_response_area.write(assistant_msg)
        end_time = time()
        # caption = f"Time: {end_time - start_time:.2f}s, Model: {llm.model_name}, Memory: {llm.load_memory()}"
        caption = f"Time: {end_time - start_time:.2f}s, Model: {llm.model_name}"
        st.caption(caption)
    return assistant_msg, caption

def save_messages(user_input, assistant_msg, caption, conversation_id):
    """メッセージの保存と表示"""
    user_id = st.session_state.user_id
    save_message("User", user_input, "", conversation_id, user_id)
    save_message("Assistant", assistant_msg, caption, conversation_id, user_id)

def initialize_session_state():
    if 'chat_log' not in st.session_state:
        st.session_state.chat_log = []
    if 'selected_conversation_id' not in st.session_state:
        st.session_state.selected_conversation_id = 'default'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'anthropic_api_key' not in st.session_state:
        st.session_state.anthropic_api_key = ""
    if 'provider' not in st.session_state:
        st.session_state.provider = PROVIDER
    if 'model' not in st.session_state:
        st.session_state.model = MODEL

def login():
    st.title("ログイン")
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if authenticate_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_id = get_user_id(username)
            st.success("ログインに成功しました")
            st.rerun()
        else:
            st.error("ユーザー名またはパスワードが間違っています")
    with st.expander("新規登録"):
        register()

def logout():
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.chat_log = []
        st.session_state.selected_conversation_id = 'default'
        st.session_state.openai_api_key = ""
        st.session_state.anthropic_api_key = ""
        st.session_state.provider = PROVIDER
        st.session_state.model = MODEL
        st.rerun()

def register():
    st.title("新規登録")
    username = st.text_input("新しいユーザー名")
    password = st.text_input("新しいパスワード", type="password")
    if st.button("登録"):
        if get_user(username):
            st.error("このユーザー名は既に使用されています")
        else:
            save_user(username, password)
            st.success("ユーザー登録に成功しました。ログインしてください。")


def setup_sidebar():
    model_config = load_model_config()
    if model_config is not None:
        providers, models = create_provider_and_model_lists(model_config)
    else:
        st.error("モデル設定の読み込みに失敗しました。")

    with st.sidebar:
        if st.button("New Chat", key="new"):
            st.session_state.selected_conversation_id = str(uuid.uuid4())
        display_conversation_history()
        
        # APIキーの入力フィールド
        user_openai_api_key = st.sidebar.text_input("OpenAI API key", st.session_state.openai_api_key, type="password")

        # 入力されたAPIキーをセッションステートに保存
        if user_openai_api_key:
            st.session_state.openai_api_key = user_openai_api_key
        if not st.session_state.openai_api_key:
            st.error("OpenAI API keyが設定されていません。")

        user_anthropic_api_key = st.sidebar.text_input("Anthropic API key", st.session_state.anthropic_api_key, type="password")
        
        if user_anthropic_api_key:
            st.session_state.anthropic_api_key = user_anthropic_api_key
        if not st.session_state.anthropic_api_key:
            st.error("Anthropic API keyが設定されていません。")

        provider = st.sidebar.selectbox("Provider", providers, index=1)
        st.session_state.provider = provider
        
        model = st.sidebar.selectbox("Model", models[provider])
        st.session_state.model = model
        
        logout()

def display_conversation_history():
    with st.expander("History"):
        user_id = st.session_state.user_id
        for conversation_id, timestamp in sorted(get_conversations(user_id), key=lambda x: x[1], reverse=True):
            formatted_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            with st.container(border=True):
                st.subheader(formatted_timestamp, divider="rainbow")
                # summary = get_summary(conversation_id) or "No summary available"
                # st.write(summary)
                if st.button("Load Chat", key=f"load-{conversation_id}"):
                    st.session_state.selected_conversation_id = conversation_id

                if st.button("Delete Chat", key=f"delete-{conversation_id}"):
                    delete_conversation(conversation_id)
                    st.rerun()

def process_conversation(conversation_id, llm):
    selected_messages = []
    if conversation_id == "new":
        conversation_id = handle_new_conversation()
    else:
        selected_messages = handle_existing_conversation(conversation_id, llm)
    user_interaction(conversation_id, llm)

def user_interaction(conversation_id, llm):
    if user_msg := st.chat_input("ここにメッセージを入力"):
        assistant_msg, caption = process_user_input(user_msg, llm)
        save_messages(user_msg, assistant_msg, caption, conversation_id)
        # 要約とその保存
        # summarize_and_save(conversation_id, llm)

def summarize_and_save(conversation_id, llm):
    """会話内容から要約を生成し、保存"""
    selected_messages = load_messages_by_conversation_id(conversation_id)
    llm.load_messages_into_memory(selected_messages)
    saved_summary = summarize(llm.load_memory())
    save_summary(saved_summary, conversation_id)
    st.rerun()


if __name__ == "__main__":
    main()
