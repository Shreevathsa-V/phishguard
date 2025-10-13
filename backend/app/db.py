from sqlmodel import SQLModel, create_engine, Session, select
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///phishguard.db")
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
