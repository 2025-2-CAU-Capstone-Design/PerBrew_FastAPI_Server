# models/review.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Review(Base):
    __tablename__ = "reviews"
    
    # Primary Key
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="CASCADE"), nullable=False, index=True)
    brew_log_id = Column(Integer, ForeignKey("brew_logs.log_id", ondelete="SET NULL"), nullable=True)
    
    # 평점 및 코멘트
    rating = Column(Integer, nullable=False)  # 1~5
    comment = Column(Text, nullable=False)
    
    # 맛 평가 (선택)
    taste_acidity = Column(Float, nullable=True)  # 1~5
    taste_sweetness = Column(Float, nullable=True)  # 1~5
    taste_bitterness = Column(Float, nullable=True)  # 1~5
    taste_body = Column(Float, nullable=True)  # 1~5
    taste_aftertaste = Column(Float, nullable=True)  # 1~5
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    recipe = relationship("Recipe", back_populates="reviews")
    
    def __repr__(self):
        return f"<Review(review_id={self.review_id}, recipe_id={self.recipe_id}, rating={self.rating})>"
