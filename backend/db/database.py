from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("Database_Url")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping= True,
)

session = sessionmaker(
    autocommit = False,
    autoflush=False,
    bind = engine
    )

Base = declarative_base()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()    


def create_table():
    from models.structure import thread,Message
    Base.metadata.create_all(bind = engine)

