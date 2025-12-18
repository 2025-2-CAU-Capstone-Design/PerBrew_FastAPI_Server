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
POST	/usr/me/info	
App	to Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: usr_id string
Body (JSON): { "taste": { "acidity": 1-5, "sweetness": 1-5, "bitterness": 1-5, "body": 1-5 }, "preferred_temperature_c": number, "grind_level": "string" }	201: { "usr_id": "string", "status": "created" }
400: { "error": "invalid_body", "message": "..." }


Personal Info update	개인 선호도 수정	
PATCH	/usr/me/info	App	Server	Headers: Authorization: Bearer <token>, Content-Type: application/json
App	to Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: usr_id string
Body (JSON): { "taste": { "acidity": 1-5, "sweetness": 1-5, "bitterness": 1-5, "body": 1-5 }, "preferred_temperature_c": number, "grind_level": "string" }	200: { "usr_id": "string", "status": "updated" }
400: { "error": "invalid_body", "message": "..." }


Get personal info	개인 선호도 확인	
GET	/usr/me/info	
App	to Server	
Headers: Authorization: Bearer <token>
Path params: usr_id string	200: { "usr_id": "string", "taste": { "acidity": 1-5, "sweetness": 1-5, "bitterness": 1-5, "body": 1-5 }, "preferred_temperature_c": number|null, "grind_level": "string|null" }
404: { "error": "user_not_found", "message": "..." }


Get log Viewer	사용자 브루잉 로그 목록 조회	
GET	/usr/me/log	
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
from app.core.auth import get_current_user  # auth 모듈에서 get_current_user 가져오기
from app.models.user import User  # User 모델 가져오기 (타입 힌팅용)
from app.models.brew_log import BrewLog as BrewLogModel
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
from app.schemas.brew_log import BrewLogCreate

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
    print("login request for : " + payload.email)
    token = UserController.login(db, payload)
    if not token:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    return token


#-----------------------------------
# 개인 정보/ 개인 선호도 조회 및 수정
#-----------------------------------
@router.get("/me/info", response_model=UserRead, status_code=status.HTTP_200_OK)
def get_user_info(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return current_user



@router.patch("/me/info", response_model=UserRead, status_code=status.HTTP_200_OK)
def update_user_info(
    payload: UserInfoUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = UserController.update_user_info(db, current_user.user_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="user_not_found")
    return updated



@router.get("/me/pref", response_model=UserPreference, status_code=status.HTTP_200_OK)
def get_user_pref(
    current_user: User = Depends(get_current_user)
):
    # DB 세션 불필요, current_user 전달
    return UserController.get_user_pref(current_user)



@router.put("/me/pref", response_model=UserPreference, status_code=status.HTTP_200_OK)
def set_user_pref(
    payload: UserPreferenceUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pref = UserController.set_user_pref(db, current_user, payload)
    if pref is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return pref


#-----------------------------------
# 사용자 브루잉 로그 목록 조회
#-----------------------------------
@router.get("/me/brew_log", response_model=PaginatedBrewLogs, status_code=status.HTTP_200_OK)
def get_brew_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = UserController.get_brew_log(db, current_user.user_id, page, page_size)
    if result is None:
        raise HTTPException(status_code=404, detail="user_not_found_or_no_logs")
    return result

# routers/brew_log.py
@router.post("/me/brew_log", status_code=status.HTTP_201_CREATED)
def create_brew_log(
    payload: BrewLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # payload contains: recipe_id, brew_id, tds, temperature_c, machine_id, etc.
    brew_log = BrewLogModel(
        user_id=current_user.user_id,
        recipe_id=payload.recipe_id,
        machine_id=payload.machine_id,
        brew_id=payload.brew_id,
        notes=payload.notes,
    )
    db.add(brew_log)
    db.commit()
    db.refresh(brew_log)
    return {"log_id": brew_log.log_id, "message": "Brew log saved"}