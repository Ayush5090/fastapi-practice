from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from typing import Optional
from app.utils import verify_token, hash_password
from uuid import uuid4
import app.models as models, app.dependencies as dependencies
import os, json

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.get('/get_user')
async def get_user(user_id: int, db: dependencies.db_dependency, payload: dict = Depends(verify_token)):

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    return {
        'success': True,
        'message': 'User found',
        'user': user.to_dict()
    }


@router.put('/update_user')
async def update_user(
    db: dependencies.db_dependency,
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


@router.delete('/delete')
async def delete_user(user_id: int, db: dependencies.db_dependency, payload: dict = Depends(verify_token)):

    user = db.query(models.Users).filter(models.Users.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    db.delete(user)
    db.commit()

    return {
        'success': True,
        'message': 'Used deleted successfully'
    }