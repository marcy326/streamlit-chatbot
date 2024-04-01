import os
from time import time
from operator import itemgetter

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from llm import LLM


# def get_state(): 
#     if "state" not in st.session_state: 
#         st.session_state.state = {"memory": ConversationBufferMemory(return_messages=True, memory_key="chat_history")} 
#         st.session_state.state["memory"].chat_memory.add_user_message("私の名前はmarcyです")
#         st.session_state.state["memory"].chat_memory.add_ai_message("marcyさんですね。よろしくお願いします。")
#     return st.session_state.state

st.title("marcy's ChatBot")

# 定数定義
USER_NAME = "user"
ASSISTANT_NAME = "assistant"
PROVIDER="OpenAI"
MODEL="gpt-3.5-turbo"
SYSTEM="必ず日本語で返答してください。"
MAX_TOKENS=2048

# uploaded_file = st.file_uploader("Upload a file after paste OpenAI API key", type="pdf")
# チャットログを保存したセッション情報を初期化
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
    
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
    select_provider = st.selectbox("Provider", ["OpenAI", "Anthropic"])
    PROVIDER = select_provider
    if PROVIDER == "OpenAI":
        select_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4-1106-preview"])
        # ChatModel = ChatOpenAI
    else:
        select_model = st.selectbox("Model", ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"])
        # ChatModel = ChatAnthropic
    MODEL = select_model
    MAX_TOKENS = st.select_slider("Max Tokens", options=[128, 256, 512, 1024, 2048, 4096], value=1024)
    select_temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.0, step=0.1,)
    # select_chunk_size = st.slider("Chunk", min_value=0.0, max_value=1000.0, value=300.0, step=10.0,)


    
llm = LLM(session_state=st.session_state, model_provider=PROVIDER, model_name=MODEL, temperature=select_temperature, system_message=SYSTEM)

# 以前のチャットログを表示
for chat in st.session_state.chat_log:
        with st.chat_message(chat["name"]):
            st.write(chat["msg"])

            if chat["caption"] is not None:
                st.caption(chat["caption"])

if user_msg := st.chat_input("ここにメッセージを入力"):
    # 最新のメッセージを表示
    t0 = time()
    with st.chat_message(USER_NAME):
        st.write(user_msg)

    user_input = [HumanMessage(content=user_msg)]
    with st.chat_message(ASSISTANT_NAME):
        assistant_msg = ""
        assistant_response_area = st.empty()
        for chunk in llm.stream(user_msg):
            assistant_msg += chunk.content
            assistant_response_area.write(assistant_msg + "▌")
        assistant_response_area.write(assistant_msg)
        t = time()-t0
        caption = f"time: {t:.1f}s, model: {select_model}"
        st.caption(caption)

    # セッションにチャットログを追加
    st.session_state.chat_log.append({"name": USER_NAME, "msg": user_msg, "caption": None})
    st.session_state.chat_log.append({"name": ASSISTANT_NAME, "msg": assistant_msg, "caption": caption})
    llm.save_memory(user_msg, assistant_msg)
