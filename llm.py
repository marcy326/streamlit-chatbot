from operator import itemgetter

from streamlit.runtime.state import SessionStateProxy

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableLambda, RunnablePassthrough


class LLM:
    def __init__(self, session_state:SessionStateProxy, model_provider="OpenAI", model_name="gpt-3.5-turbo", temperature=0, system_message=""):
        self.model_provider = model_provider
        self.model_name = model_name
        self.temperature = temperature
        self.system_message = system_message
        self.session_state = session_state
        self.__init_state()
        self.prompt = self.__setting_prompt()
        self.model = self.__setting_model()
        self.chain = self.__setting_chain()
    
    def __init_state(self): 
        session_state = self.session_state
        if "state" not in session_state: 
            self.state = {"memory": ConversationBufferMemory(return_messages=True, memory_key="chat_history")}
            for human_message, ai_message in zip(session_state.chat_log[::2], session_state.chat_log[1::2]):
                self.save_memory(human_message["message"], ai_message["message"])
    
    def __setting_prompt(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}" )
        ])
        return prompt
    
    def __setting_model(self):
        if self.model_provider == "OpenAI":
            ChatModel = ChatOpenAI
        elif self.model_provider == "Anthropic":
            ChatModel = ChatAnthropic

        model = ChatModel(model_name=self.model_name, temperature=self.temperature, streaming=True)
        return model
    
    def __setting_chain(self):
        state = self.state
        chain = (
            RunnablePassthrough.assign(
                chat_history=RunnableLambda(state["memory"].load_memory_variables) | itemgetter("chat_history")
            )
            | self.prompt
            | self.model
        )
        return chain
    
    def stream(self, input):
        chain = self.chain
        stream = chain.stream({'input': input})
        return stream
    
    def save_memory(self, input, output):
        state = self.state
        state["memory"].save_context({"input": input}, {"output": output})

    def load_memory(self):
        state = self.state
        return state['memory'].load_memory_variables({})
