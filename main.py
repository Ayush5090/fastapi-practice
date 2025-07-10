from fastapi import FastAPI, HTTPException, Depends, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from utils import create_access_token, verify_token, hash_password, verify_password
from database import engine, SessionLocal
from uuid import uuid4
import models, os, json

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

class Addresses(BaseModel):
    user_id: int
    city: str
    state: str
    country: str

class UserModel(BaseModel):
    name: str
    email: str
    password: str
    address: Addresses


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


@app.get('/user')
async def get_user(user_id: int, db: db_dependency, payload: dict = Depends(verify_token)):

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    return {
        'success': True,
        'message': 'User found',
        'user': user.to_dict()
    }


@app.put('/update_user')
async def update_user(
    db: db_dependency,
    name: Optional[str] = Form(None), 
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    address: Optional[str] = Form(None),
    payload: dict = Depends(verify_token),
):

    user_id = payload.get('id')

    if not user_id:
        raise HTTPException(status_code=404, detail='Invalid token, User id not found')
    
    update_data = {}

    if name is not None:
        update_data['name'] = name
    if email is not None:
        update_data['email'] = email
    if password is not None:
        update_data['password'] = hash_password(password)

    updated_address = {}
    if address is not None:
        try:
            address_data = json.loads(address)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid address format, expected JSON')
        
        if "city" in address_data and address_data["city"] is not None:
            updated_address['city'] = address_data['city']

        if 'state' in address_data and address_data['city'] is not None:
            updated_address['state'] = address_data['state']

        if 'country' in address_data and address_data['country'] is not None:
            updated_address['country'] = address_data['country']

        if updated_address is not None:
            existing_address = db.query(models.Addresses).filter(models.Addresses.user_id == user_id).first()

            if existing_address:
                db.query(models.Addresses).filter(models.Addresses.user_id == user_id).update(updated_address)
            else:
                updated_address['user_id'] = user_id
                new_address = models.Addresses(**updated_address)
                db.add(new_address)
            db.commit()

    if profile_image:
        MAX_FILE_SIZE = 5 * 1024 * 1024
        UPLOAD_DIR = "uploads/profile_images"
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        content = await profile_image.read()

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400,
            detail=f'Image file size exceeds limit of {MAX_FILE_SIZE // (1024 * 1024)}MB')
        
        allowed_extensions = {'.jpg', '.jpeg', '.png'}
        file_ext = os.path.splitext(profile_image.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400,
            detail='Invalid image format. Only JPG, JPEG and PNG are allowed.')
        
        file_name = f'{uuid4()}{file_ext}'
        file_path = os.path.join(UPLOAD_DIR, file_name)

        try:
            with open(file_path, 'wb') as buffer:
                buffer.write(content)

            update_data['profile_image'] = f'/{UPLOAD_DIR}/{file_name}'

        except Exception as e:
            raise HTTPException(status_code=500, detail={
                'success': False,
                'message': 'Failed to save profile image file.',
                'error': str(e)
            })
                
    if not update_data and not updated_address:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    
    db.query(models.Users).filter(models.Users.id == user_id).update(update_data)
    db.commit()
    
    return {
        'success': True,
        'message': 'User updated successfully',
        'user': {
            'name': name,
            'email': email,
            'profile_image': update_data.get('profile_image'),
            'address': updated_address if updated_address else None
        }
    }


@app.delete('/delete')
async def delete_user(user_id: int, db: db_dependency, payload: dict = Depends(verify_token)):

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    db.delete(user)
    db.commit()

    return {
        'success': True,
        'message': 'Used deleted successfully'
    }