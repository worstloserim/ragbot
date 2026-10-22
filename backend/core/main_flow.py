from langgraph.graph import StateGraph,START,END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage,BaseMessage

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from langchain_groq import ChatGroq

from typing import Annotated,Literal,TypedDict
from dotenv import load_dotenv

import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
database_url = os.environ["DATABASE_URL"]

llm = ChatGroq( model="openai/gpt-oss-20b",api_key= api_key)


class chatstate(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]


def chat(State : chatstate):
    messages = State["messages"]

    response = llm.invoke(messages)

    return {'messages' : [response]}


pool = ConnectionPool(
    conninfo=database_url,
    kwargs={"autocommit": True, "row_factory": dict_row},
    open=True,
)

checkpointer = PostgresSaver(pool)
checkpointer.setup()


graph = StateGraph(chatstate)

graph.add_node("chat",chat)

graph.add_edge(START,"chat")
graph.add_edge("chat",END)
 

chatbot = graph.compile(checkpointer= checkpointer)