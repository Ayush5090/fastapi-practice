from pydantic import BaseModel
from typing import Optional

class Addresses(BaseModel):
    user_id: int
    city: str
    state: str
    country: str

class UserModel(BaseModel):
    name: str
    email: str
    password: str
    address: Optional[Addresses] = None