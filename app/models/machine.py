# models/machine.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum

class BrewPhaseEnum(str, enum.Enum):
    idle = "idle"
    rinsing = "rinsing"
    blooming = "blooming"
    pouring = "pouring"
    done = "done"
    error = "error"


class Machine(Base):
    __tablename__ = "machines"
    
    # Primary Key
    machine_id = Column(String(100), primary_key=True)
    
    # Foreign Key
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 머신 정보
    email = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    
    # 상태 관리
    current_phase = Column(Enum(BrewPhaseEnum), default=BrewPhaseEnum.idle, nullable=False)
    last_brew_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 펌웨어
    firmware_version = Column(String(50), nullable=True)
    
    # 타임스탬프
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="machines")
    brew_logs = relationship("BrewLog", back_populates="machine")
    
    def __repr__(self):
        return f"<Machine(machine_id={self.machine_id}, user_id={self.user_id})>"