# models/user.py
from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    # Primary Key // 
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 기본 정보
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(100), nullable=True)
    
    # Relationships
    preference = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    recipes = relationship("Recipe", back_populates="owner", cascade="all, delete-orphan")
    machines = relationship("Machine", back_populates="user", cascade="all, delete-orphan")
    brew_logs = relationship("BrewLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email})>"


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    # Primary Key (1:1 relationship with User)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    
    # 맛 선호도 (1~5)
    acidity = Column(Float, nullable=True)
    sweetness = Column(Float, nullable=True)
    bitterness = Column(Float, nullable=True)
    body = Column(Float, nullable=True)
    
    # 추출 선호도
    preferred_temperature_c = Column(Float, nullable=True)
    grind_level = Column(String(50), nullable=True)  # coarse, medium, fine
    
    # Relationships
    user = relationship("User", back_populates="preference")
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id})>"
