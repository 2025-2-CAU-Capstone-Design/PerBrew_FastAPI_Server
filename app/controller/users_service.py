from sqlalchemy.orm import Session
from app.models.user import User
from app.models.brew_log import BrewLog

from sqlalchemy import desc, func

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
    def update_user_info(db: Session, user: User, payload: UserInfoUpdate):
        
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
    def get_user_pref(user: User):
        return user  # User 모델에 선호도 필드가 포함되어 있음


    @staticmethod
    def set_user_pref(db: Session, user: User, payload: UserPreferenceUpdate):
        # user_id로 다시 조회하지 않고 전달받은 user 객체 사용
        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
            
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_brew_log(db: Session, user_id: str, page: int = 1, page_size: int = 20):
        """
        사용자별 브루잉 로그를 페이지네이션하여 조회
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100  # 최대 100개 제한 (보안/성능)

        offset = (page - 1) * page_size
        print("user_id:", user_id, "page:", page, "page_size:", page_size, "offset:", offset)
        # 총 개수 조회
        total = db.query(func.count(BrewLog.log_id)) \
                .filter(BrewLog.user_id == user_id) \
                .scalar()

        # 로그 목록 조회 (최신순 정렬)
        items = db.query(BrewLog) \
                .filter(BrewLog.user_id == user_id) \
                .order_by(desc(BrewLog.brewed_at)) \
                .offset(offset) \
                .limit(page_size) \
                .all()

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total or 0,
            "total_pages": (total + page_size - 1) // page_size if total else 0  # 선택사항
        }