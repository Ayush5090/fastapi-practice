from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
from utils import create_access_token, verify_token, hash_password, verify_password
import models, json
from database import engine, SessionLocal

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.exception_handler(HTTPException)
async def custom_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", str(exc.detail))}
    )


class UserModel(BaseModel):
    name: str
    email: str
    password: str

class Addresses(BaseModel):
    user_id: int
    city: str
    state: str
    country: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post('/signup/')
async def signup(user: UserModel, db: db_dependency):
    db_user = models.Users(name = user.name, email = user.email, password = hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        'success': True,
        'message': 'User signed up successfully',
        'user': user
    }


@app.get('/login/')
async def login(email: str, password: str, db: db_dependency):
    user = db.query(models.Users).filter(models.Users.email == email).first()

    if user is None:
        raise HTTPException(status_code=404, detail='User not found, Please sign up to create account.')

    if verify_password(password, user.password):
        token = create_access_token(user.to_dict())
        return {
            "success": True,
            "message": "Login successfull",
            "token": token
        }
    else:
        raise HTTPException(status_code=401, detail='Wrong password entered')


@app.put('/update_user')
async def update_user(updated_user: UserModel, db: db_dependency, payload: dict = Depends(verify_token)):

    user_id = payload.get('id')

    if not user_id:
        raise HTTPException(status_code=404, detail='Invalid token, User id not found')
    
    user = db.query(models.Users).filter(models.Users.id == user_id).update({
        "name": updated_user.name,
        "email": updated_user.email,
        "password": updated_user.password
    })

    db.commit()

    return {
        'success': True,
        'message': 'User updated successfully',
        'user': updated_user
    }