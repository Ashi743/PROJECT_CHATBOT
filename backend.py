from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from langgraph.graph import StateGraph, START ,END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from typing import TypedDict ,Annotated 
from dotenv import load_dotenv


load_dotenv()

llm_model= ChatOpenAI()

class chatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state:chatState):
    message= state["messages"]
    response =llm_model.invoke(message)
    return {'messages': [response]}

## -------------------- MEMORY CHECKPOINTING --------------------
checkpointer= InMemorySaver()
## --------------------------------------------------------------

graph= StateGraph(chatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot =graph.compile(checkpointer=checkpointer)