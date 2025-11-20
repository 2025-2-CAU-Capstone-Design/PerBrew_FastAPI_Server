from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


#----------------------------------------
# Request DTOs - 요청 객체
#----------------------------------------
#Auth
class UserSignUp(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

#User Info
class UserInfoUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    username : Optional[str] = None

#User Preference
class UserPreferenceUpdate(BaseModel):
    acidity: Optional[float] = None
    sweetness: Optional[float] = None
    bitterness: Optional[float] = None
    body: Optional[float] = None
    preferred_temperature_c: Optional[float] = None
    grind_level: Optional[str] = None

#----------------------------------------
# Response DTOs - 응답 객체
#----------------------------------------

class UserRead(BaseModel):
    id: str
    email: EmailStr
    username: Optional[str] = None

class UserPreference(BaseModel):
    acidity: Optional[float] = None
    sweetness: Optional[float] = None
    bitterness: Optional[float] = None
    body: Optional[float] = None
    preferred_temperature_c: Optional[float] = None
    grind_level: Optional[str] = None

#Brew Log
class UserBrewLog(BaseModel):
    brew_id: str
    recipe_id: str
    rating: Optional[int] = None
    created_at: str

class TokenResponse(BaseModel):
    user: UserRead
    access_token: str
    expires_in_s: int

class PaginatedBrewLogs(BaseModel):
    items: List[UserBrewLog]
    page: int
    page_size: int
    total: Optional[int] = None