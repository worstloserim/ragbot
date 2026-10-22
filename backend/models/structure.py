from sqlalchemy import String,Integer,Delete,ForeignKey,DateTime,func,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship

from datetime import datetime

import uuid
from sqlalchemy.dialects.postgresql import UUID

from db.database import Base

class thread(Base):
    __tablename__ = "thread"

    id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        )
    title : Mapped[str] = mapped_column( String(255),default="New Chat")

    created_at : Mapped[datetime] = mapped_column(
         DateTime(timezone=True),
         server_default=func.now()
           )
    messages : Mapped[list["Message"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="Message.id", )


class Message(Base) :
    __tablename__ = "Message"    
    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("thread.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    thread: Mapped["thread"] = relationship(
        back_populates="messages"
    )


