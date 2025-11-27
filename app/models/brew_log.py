# models/brew_log.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum

class BrewPhaseEnum(str, enum.Enum):
    """브루잉 단계 상태"""
    idle = "idle"
    rinsing = "rinsing"
    blooming = "blooming"
    pouring = "pouring"
    done = "done"
    error = "error"


class BrewLog(Base):
    __tablename__ = "brew_logs"
    
    # Primary Key
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="SET NULL"), nullable=True, index=True)
    bean_id = Column(Integer, ForeignKey("coffee_beans.bean_id", ondelete="SET NULL"), nullable=True)
    machine_id = Column(String(100), ForeignKey("machines.machine_id", ondelete="SET NULL"), nullable=True)
    
    # 브루잉 고유 ID (머신에서 생성한 ID)
    brew_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # 브루잉 결과 데이터 (MachineBrewLog.result에서 가져온 필드들)
    tds = Column(Float, nullable=True)  # Total Dissolved Solids
    temperature_c = Column(Float, nullable=True)  # 최종 온도
    notes = Column(Text, nullable=True)  # 메모
    
    # 타임스탬프
    brewed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="brew_logs")
    recipe = relationship("Recipe", back_populates="brew_logs")
    bean = relationship("CoffeeBean", back_populates="brew_logs")
    machine = relationship("Machine", back_populates="brew_logs")
    
    def __repr__(self):
        return f"<BrewLog(log_id={self.log_id}, brew_id={self.brew_id}, user_id={self.user_id})>"
