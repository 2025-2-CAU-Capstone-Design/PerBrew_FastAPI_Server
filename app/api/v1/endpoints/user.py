from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.user import UserCreate, UserRead
from app.crud.user import get_user, create_user, get_users
from app.api.deps import get_db

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=201) # /users 경로(상위 prefix가 /users)에 POST 요청 처리
def create_new_user(user: UserCreate, db: Session = get_db()):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db, user)

@router.get("/", response_model=List[UserRead]) # 응답을 pydantic 모델 UserRead 리스트로 변환
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)): # Depends로 DB 세션 주입받고 CRUD 함수에 전달
    users = get_users(db, skip=skip, limit=limit)
    return users
    