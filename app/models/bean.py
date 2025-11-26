# models/bean.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class CoffeeBean(Base):
    __tablename__ = "coffee_beans"
    
    # Primary Key
    bean_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 기본 정보 (필수)
    bean_name = Column(String(200), nullable=False)
    origin = Column(String(100), nullable=False)  # 원산지
    roast_level = Column(Integer, nullable=False)  # 1~5 (약→강)
    
    # 상세 정보 (선택)
    roast_date = Column(Date, nullable=True)
    processing_method = Column(String(100), nullable=True)  # washed, natural, honey
    elevation_masl = Column(Integer, nullable=True)  # meters above sea level
    
    # 플레이버 노트 (JSON 배열로 저장)
    flavor_notes = Column(JSON, nullable=True)  # ["chocolate", "berry", "floral"]
    
    # 설명
    description = Column(Text, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    recipes = relationship("Recipe", back_populates="bean")
    brew_logs = relationship("BrewLog", back_populates="bean")
    
    def __repr__(self):
        return f"<CoffeeBean(bean_id={self.bean_id}, name={self.bean_name}, origin={self.origin})>"
