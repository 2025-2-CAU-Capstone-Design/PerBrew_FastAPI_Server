from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import (
    UserSignUp, 
    UserLogin, 
    UserInfoUpdate, 
    UserPreferenceUpdate
)
from app.core.auth import get_password_hash, verify_password, create_access_token
from app.core.config import settings

class UserController:
    @staticmethod
    def signup(db: Session, payload: UserSignUp):
        check_user = db.query(User).filter(User.email == payload.email).first()
        if check_user:
            return None
        hashed_password = get_password_hash(payload.password)
        new_user = User(
            user_id = payload.user_id,
            email=payload.email,
            username = payload.username,
            password_hash = hashed_password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    @staticmethod
    def login(db: Session, payload: UserLogin):
        user = db.query(User).filter(User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.password_hash):
            return None
        
        access_token = create_access_token(data={"sub": user.email, "user_id": user.user_id})

        return {
            "user": user,
            "access_token": access_token,
            "expires_in_s": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def get_user_info(db: Session, user_id: str):
        return db.query(User).filter(User.user_id == user_id).first()


    @staticmethod
    def update_user_info(db: Session, user_id: str, payload: UserInfoUpdate):
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        
        # 값이 있는 필드만 업데이트
        if payload.username is not None:
            user.username = payload.username
        if payload.email is not None:
            user.email = payload.email
        if payload.password is not None:
            user.password_hash = get_password_hash(payload.password)
            
        db.commit()
        db.refresh(user)
        return user


    @staticmethod
    def get_user_pref(db: Session, user_id: str):
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        return user  # User 모델에 선호도 필드가 포함되어 있음


    @staticmethod
    def set_user_pref(db: Session, user_id: str, payload: UserPreferenceUpdate):
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return None
        
        # Pydantic 모델에서 설정된 값만 추출하여 업데이트
        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
            
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_brew_log(db: Session, user_id: str, page: int, page_size: int):
        # 아직 BrewLog 모델이 연동되지 않았으므로 빈 결과 반환 (추후 구현)
        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": 0
        }   