from typing import Annotated
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]