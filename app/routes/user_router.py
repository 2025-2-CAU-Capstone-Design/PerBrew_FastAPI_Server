"""
login	로그인	
POST	/login	
App	to Server	
Headers: Content-Type: application/json
Body (JSON): { "email": "string", "password": "string" }
Example: { "email": "user@example.com", "password": "secret1234" }	200: { "user": { "id": "string", "email": "string", "name": "string|null" }, "token": "jwt", "expires_in_s": 3600 }
401: { "error": "invalid_credentials", "message": "..." }


signup	회원가입	
POST	/signup	
App to Server	
Headers: Content-Type: application/json
Body (JSON): { "email": "string", "password": "string", "name": "string" }	201: { "user": { "id": "string", "email": "string", "name": "string" }, "token": "jwt" }
409: { "error": "email_in_use", "message": "..." }


Personal Info Registration	개인 선호도 등록	
POST	/usr/{usr_id}/info	
App	to Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: usr_id string
Body (JSON): { "taste": { "acidity": 1-5, "sweetness": 1-5, "bitterness": 1-5, "body": 1-5 }, "preferred_temperature_c": number, "grind_level": "string" }	201: { "usr_id": "string", "status": "created" }
400: { "error": "invalid_body", "message": "..." }


Personal Info update	개인 선호도 수정	
PATCH	/usr/{usr_id}/info	App	Server	Headers: Authorization: Bearer <token>, Content-Type: application/json
App	to Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: usr_id string
Body (JSON): { "taste": { "acidity": 1-5, "sweetness": 1-5, "bitterness": 1-5, "body": 1-5 }, "preferred_temperature_c": number, "grind_level": "string" }	200: { "usr_id": "string", "status": "updated" }
400: { "error": "invalid_body", "message": "..." }


Get personal info	개인 선호도 확인	
GET	/usr/{usr_id}/info	
App	to Server	
Headers: Authorization: Bearer <token>
Path params: usr_id string	200: { "usr_id": "string", "taste": { "acidity": 1-5, "sweetness": 1-5, "bitterness": 1-5, "body": 1-5 }, "preferred_temperature_c": number|null, "grind_level": "string|null" }
404: { "error": "user_not_found", "message": "..." }


Get log Viewer	사용자 브루잉 로그 목록 조회	
GET	/usr/{usr_id}/log	
App to Server	
Headers: Authorization: Bearer <token>
Path params: usr_id string
Query: page integer(1), page_size integer(20)	200: { "items": [ { "brew_id": "string", "recipe_id": "string", "rating": integer|null, "created_at": "ISO-8601" } ], "page": 1, "page_size": 20, "total": 0 }
404: { "error": "user_not_found", "message": "..." }


Put Update User Information	유저 개인정보 업데이트	
PUT	/sur/{user_id}/update				

"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.controller.users_service import UserController
from app.schemas.user_schema import (
    UserSignUp,
    UserLogin,
    UserInfoUpdate,
    UserPreferenceUpdate,
    UserPreference,
    UserRead,
    TokenResponse,
    PaginatedBrewLogs,
)

router = APIRouter()

#-----------------------------------
# 회원가입 / 로그인 / 개인정보 업데이트
#-----------------------------------
@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignUp, db: Session = Depends(get_db)):
    created = UserController.signup(db, payload)
    if not created:
        raise HTTPException(status_code=409, detail="email_in_use")
    return created

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    token = UserController.login(db, payload)
    if not token:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    return token


#-----------------------------------
# 개인 정보/ 개인 선호도 조회 및 수정
#-----------------------------------
@router.get("/{usr_id}/info", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_user_info(usr_id: str, db: Session = Depends(get_db)):
    user = UserController.get_user_info(db, usr_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user

@router.patch("/{usr_id}/info", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_user_info(usr_id: str, payload: UserInfoUpdate, db: Session = Depends(get_db)):
    updated = UserController.update_user_info(db, usr_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="user_not_found")
    return updated

@router.get("/{usr_id}/pref", response_model=UserPreference, status_code=status.HTTP_200_OK)
def get_user_pref(usr_id: str, db: Session = Depends(get_db)):
    pref = UserController.get_user_pref(db, usr_id)
    if pref is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return pref

@router.put("/{usr_id}/pref", response_model=UserPreference, status_code=status.HTTP_200_OK)
def set_user_pref(usr_id: str, payload: UserPreferenceUpdate, db: Session = Depends(get_db)):
    pref = UserController.set_user_pref(db, usr_id, payload)
    if pref is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return pref


#-----------------------------------
# 사용자 브루잉 로그 목록 조회
#-----------------------------------
@router.get("/{usr_id}/brew_log", response_model=PaginatedBrewLogs, status_code=status.HTTP_200_OK)
def get_brew_log(
    usr_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    result = UserController.get_brew_log(db, usr_id, page, page_size)
    if result is None:
        raise HTTPException(status_code=404, detail="user_not_found_or_no_logs")
    return result