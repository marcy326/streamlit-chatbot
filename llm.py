# llm.py
from operator import itemgetter

from streamlit.runtime.state import SessionStateProxy

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

USER_NAME = "user"
ASSISTANT_NAME = "assistant"

class LLM:
    def __init__(self, model_provider="OpenAI", model_name="gpt-3.5-turbo", temperature=0, system_message="", openai_api_key=None, anthropic_api_key=None):
        self.model_provider = model_provider
        self.model_name = model_name
        self.temperature = temperature
        self.system_message = system_message
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        # ここでメモリの初期化を行う
        self.state = {"memory": ConversationBufferWindowMemory(k=10, return_messages=True, memory_key="chat_history")}
        self.prompt = self.__setting_prompt()
        self.model = self.__setting_model()
        self.chain = self.__setting_chain()
    
    def __setting_prompt(self):
        # プロンプトの設定
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        return prompt
    
    def __setting_model(self):
        # モデルの設定
        if self.model_provider == "OpenAI":
            ChatModel = ChatOpenAI
            model = ChatModel(model_name=self.model_name, temperature=self.temperature, streaming=True, openai_api_key=self.openai_api_key)
        elif self.model_provider == "Anthropic":
            ChatModel = ChatAnthropic
            model = ChatModel(model_name=self.model_name, temperature=self.temperature, streaming=True, anthropic_api_key=self.anthropic_api_key)
        return model
    
    def __setting_chain(self):
        # 実行チェーンの設定
        chain = (
            RunnablePassthrough.assign(
                chat_history=RunnableLambda(self.state["memory"].load_memory_variables) | itemgetter("chat_history")
            )
            | self.prompt
            | self.model
        )
        return chain
    
    def stream(self, input_text):
        # 入力テキストに対するストリーム応答
        return self.chain.stream({'input': input_text})

    def invoke(self, input_text):
        # 入力テキストに対する一回の応答
        return self.chain.invoke({'input': input_text})

    def save_memory(self, input_text, output_text):
        # 会話のメモリへの保存
        self.state["memory"].save_context({"input": input_text}, {"output": output_text})

    def load_memory(self):
        # メモリの読み込み
        return self.state["memory"].load_memory_variables({})

    def load_messages_into_memory(self, messages):
        # メッセージリストをメモリにロード
        self.reset_memory()
        # messagesリストがユーザーのメッセージとAIの応答のペアを含んでいると仮定して処理
        for i in range(0, len(messages), 2):
            user_message = messages[i]["message"]  # ユーザーからのメッセージ
            if i + 1 < len(messages):
                ai_response = messages[i + 1]["message"]  # AIからの応答
            else:
                ai_response = ""  # 最後のメッセージがユーザーからの場合、AIの応答は空
            self.save_memory(user_message, ai_response)

    def reset_memory(self):
        # メモリのリセット
        self.state["memory"].clear()

_system_message = """
    ルール：
    - 会話の見出しとして使用するため、要約の結果のみを20文字以内で簡潔に出力してください。
    - 会話履歴にトピックが複数含まれている場合には、
        1.それらのトピックが類似している場合は抽象化して一つのテーマとしてください。
        2.それらのトピックが類似していない場合はそれらから最新のトピックを1個抽出して要約してください。
        *ここで最新とは、会話履歴のうち、一番最後のものです。
    - アシスタントの返答内容ではなく、特にユーザーがどのような質問をしているかという点に注目して要約してください。
    - 体言止めにしてください。
    - 返事など余分な言葉は出力しないでください。
    - 会話履歴と含まれない内容を出力しないでください。
    """

def summarize(conversation_text, model_provider="OpenAI", model_name="gpt-4o-mini", temperature=0, system_message=_system_message):
    """
    会話テキストから要約を生成する。
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, temperature=temperature, system_message=system_message)
    summary = llm.invoke(conversation_text).content
    return summary