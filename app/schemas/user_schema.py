from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Auth
class UserSignUp(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# User Update
class UserInfoUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    username: Optional[str] = None


class UserPreferenceUpdate(BaseModel):
    acidity: Optional[float] = None
    sweetness: Optional[float] = None
    bitterness: Optional[float] = None
    body: Optional[float] = None
    preferred_temperature_c: Optional[float] = None
    grind_level: Optional[str] = None


# Responses
class UserRead(BaseModel):
    user_id: str
    email: EmailStr
    username: Optional[str]

    class Config:
        orm_mode = True


class UserPreference(BaseModel):
    acidity: Optional[float]
    sweetness: Optional[float]
    bitterness: Optional[float]
    body: Optional[float]
    preferred_temperature_c: Optional[float]
    grind_level: Optional[str]

    class Config:
        orm_mode = True


class UserBrewLog(BaseModel):
    log_id: int
    brew_id: str
    recipe_id: Optional[int]
    bean_id: Optional[int]
    machine_id: Optional[str]
    tds: Optional[float]
    temperature_c: Optional[float]
    notes: Optional[str]
    brewed_at: datetime

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    user: UserRead
    access_token: str
    expires_in_s: int


class PaginatedBrewLogs(BaseModel):
    items: List[UserBrewLog]
    page: int
    page_size: int
    total: Optional[int]
