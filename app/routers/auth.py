from fastapi import APIRouter, HTTPException
from app.utils import create_access_token, hash_password, verify_password
import app.models as models, app.dependencies as dependencies, app.schemas as schemas

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/signup/')
async def signup(user: schemas.UserModel, db: dependencies.db_dependency):

    is_present = db.query(models.Users).filter(models.Users.email == user.email).first()

    if is_present:
        raise HTTPException(status_code=409, detail='An account already exists with given email')

    db_user = models.Users(name = user.name, email = user.email, password = hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        'success': True,
        'message': 'User signed up successfully',
        'user': user
    }


@router.get('/login/')
async def login(email: str, password: str, db: dependencies.db_dependency):
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