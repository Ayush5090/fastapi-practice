from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timezone, timedelta
import jwt, json
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

SECRET_KEY = 'JWT_SECRET'
ALOGRITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


def create_access_token(data: dict) -> str:
     """
    Create a JWT access token with an expiration time using PyJWT.
    
    Args:
        data: Payload data to encode (e.g., {"sub": "user@example.com"})
    
    Returns:
        str: Encoded JWT token
    """
     expire = datetime.now(timezone.utc) + timedelta(weeks= ACCESS_TOKEN_EXPIRE_MINUTES)
     data.update({"exp": expire})
     encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALOGRITHM)
     return encoded_jwt


async def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decode a JWT token and return the payload upon successful decoding.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        dict: Decoded token payload
    
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token, Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALOGRITHM])
        if not payload.get("id"):
            raise credentials_exception
        return payload
    
    except jwt.InvalidTokenError:
        raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
   
    

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Args:
        password: Plain-text password to hash
    
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.
    
    Args:
        plain_password: Plain-text password to verify
        hashed_password: Hashed password from the database
    
    Returns:
        bool: True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)