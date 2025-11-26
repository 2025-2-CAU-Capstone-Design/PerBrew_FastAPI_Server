# models/recipe.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
import enum

class Recipe(Base):
    __tablename__ = "recipes"
    
    # Primary Key
    recipe_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 기본 정보
    recipe_name = Column(String(200), nullable=False)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    bean_id = Column(Integer, ForeignKey("coffee_beans.bean_id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 공개 설정
    is_public = Column(Boolean, default=False, nullable=False)
    
    # 추출 파라미터 (필수)
    dose_g = Column(Float, nullable=False)  # 원두량
    water_temperature_c = Column(Float, nullable=False)  # 물 온도
    total_water_g = Column(Float, nullable=True)  # 총 물 양
    total_brew_time_s = Column(Float, nullable=True)  # 총 추출 시간
    
    # 분쇄도
    grind_level = Column(String(50), nullable=True)  # coarse, medium, fine
    grind_microns = Column(Integer, nullable=True)  # 미크론 단위
    
    # 추가 옵션
    rinsing = Column(Boolean, default=False, nullable=False)  # 린싱 여부
    
    # 출처 정보
    source = Column(String(200), nullable=True)  # 레시피 출처
    url = Column(Text, nullable=True)  # 크롤링된 URL
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="recipes")
    bean = relationship("CoffeeBean", back_populates="recipes")
    pouring_steps = relationship("PouringStep", back_populates="recipe", cascade="all, delete-orphan", order_by="PouringStep.step_number")
    brew_logs = relationship("BrewLog", back_populates="recipe")
    reviews = relationship("Review", back_populates="recipe")
    
    def __repr__(self):
        return f"<Recipe(recipe_id={self.recipe_id}, name={self.recipe_name})>"


class TechniqueEnum(str, enum.Enum):
    center = "center"
    spiral_out = "spiral_out"
    pulse = "pulse"


class PouringStep(Base):
    __tablename__ = "pouring_steps"
    
    # Primary Key
    pouring_step_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 단계 정보
    step_number = Column(Integer, nullable=False)  # 주입 순서
    water_g = Column(Float, nullable=False)  # 이번 단계 물 양
    pour_time_s = Column(Float, nullable=False)  # 주입 시간
    wait_time_s = Column(Float, nullable=True)  # 대기 시간
    bloom_time_s = Column(Float, nullable=True)  # 블루밍 시간
    technique = Column(Enum(TechniqueEnum), nullable=True)  # center, spiral_out, pulse
    
    # Relationships
    recipe = relationship("Recipe", back_populates="pouring_steps")
    
    def __repr__(self):
        return f"<PouringStep(recipe_id={self.recipe_id}, step={self.step_number})>"
