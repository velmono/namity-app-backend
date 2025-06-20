from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserRead(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

class Token(BaseModel):
    access_token: str
    refresh_token: str
    id_token: Optional[str] = None

class TokenRequest(BaseModel):
    email: EmailStr
    password: str
    scope: Optional[List[str]] = []

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(Token):
    pass

class ChangePassword(BaseModel):
    old_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")