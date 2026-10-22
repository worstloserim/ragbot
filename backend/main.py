from fastapi import FastAPI,HTTPException,status,Depends
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel,Field

from sqlalchemy.orm import Session,query
from sqlalchemy import select

from db.database import get_db,create_table
from models import structure
from models.structure import thread,Message

from langchain_core.messages import HumanMessage
from core.main_flow import chatbot
from langchain_core.messages import HumanMessage

from uuid import UUID
import uuid


app = FastAPI(
    title="Rag_bot",
    description="CHAT_BOT",
    version= "0.1.0",
    docs_url= "/docs",
    redoc_url= "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    
);



class MessageCreate(BaseModel):
    role: str
    content: str = Field(min_length=1)

@app.get("/")
def try_gma():
    return "hello"  

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    create_table()


# 1. Create a new conversation
@app.post("/threads", status_code=status.HTTP_201_CREATED)
def create_thread(db: Session = Depends(get_db)):
    thread = structure.thread(title="New Chat")
    db.add(thread)
    db.commit()
    db.refresh(thread)

    return {
        "id": str(thread.id),
        "title": thread.title,
        "created_at": thread.created_at,
    }


# 2. List conversations for the sidebar
@app.get("/threads")
def list_threads(db: Session = Depends(get_db)):
    statement = (
        select(structure.thread)
        .order_by(structure.thread.created_at.desc())
    )
    threads = db.scalars(statement).all()

    return [
        {
            "id": str(thread.id),
            "title": thread.title,
            "created_at": thread.created_at,
        }
        for thread in threads
    ]


# 3. Save a message to a conversation
@app.post("/threads/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
def add_message(
    thread_id: UUID,
    data: MessageCreate,
    db: Session = Depends(get_db),
):
    if data.role != "user":
        raise HTTPException(
            status_code=400,
            detail="Send a user message; the assistant response is generated automatically.",
        )

    chat_thread = db.get(thread, thread_id)
    if chat_thread is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Send the user's message to LangGraph.
    result = chatbot.invoke(
        {"messages": [HumanMessage(content=data.content)]},
        {"configurable": {"thread_id": str(thread_id)}},
    ),
    if isinstance(result, tuple):
        result = result[0]

        assistant_text = result["messages"][-1].content

    # Save both messages in your application's Message table.
    user_message = Message(
        thread_id=thread_id,
        role="user",
        content=data.content,
    )
    assistant_message = Message(
        thread_id=thread_id,
        role="assistant",
        content=assistant_text,
    )

    db.add_all([user_message, assistant_message])

    # Set the title from the first user message.
    if chat_thread.title == "New Chat":
        chat_thread.title = data.content[:60]

    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return {
        "user_message": {
            "id": user_message.id,
            "role": user_message.role,
            "content": user_message.content,
        },
        "assistant_message": {
            "id": assistant_message.id,
            "role": assistant_message.role,
            "content": assistant_message.content,
        },
    }


# 4. Load messages when opening a conversation
@app.get("/threads/{thread_id}/messages")
def get_messages(
    thread_id: UUID,
    db: Session = Depends(get_db),
):
    thread = db.get(structure.thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in thread.messages
    ]


# 5. Delete a conversation
@app.delete("/threads/{thread_id}")
def delete_thread(
    thread_id: UUID,
    db: Session = Depends(get_db),
):
    thread = db.get(structure.thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(thread)
    db.commit()

    return {"message": "Chat deleted successfully"}



if __name__ =="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port = 8000,reload = True)