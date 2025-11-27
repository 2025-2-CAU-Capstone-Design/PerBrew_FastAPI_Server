from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user_schema import (
    UserSignUp, 
    UserLogin, 
    UserInfoUpdate, 
    UserPreferenceUpdate
)
from app.schemas.review_schema import (
    ReviewCreate,    # { user_id, recipe_id, rating, comment }
    Review,
    PaginatedReviews,
)
from app.core.auth import get_password_hash, verify_password, create_access_token
from app.core.config import settings

class ReviewController:
    @staticmethod
    def create_review(payload: ReviewCreate, db:Session):
        new_review = Review(
            user_id = payload.user_id,
            recipe_id = payload.recipe_id,
            rating = payload.rating,
            comment = payload.comment
        )
        if not new_review:
            return None
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        return new_review
    
    @staticmethod
    def get_review_list(page: int, page_size: int, db:Session):
        query = db.query(Review)
        total = query.count()
        reviews = query.offset((page -1) * page_size).limit(page_size).all()
        if reviews is None:
            return None
        return {
            "items": reviews,
            "page": page,
            "page_size": page_size,
            "total": total
        }

    @staticmethod
    def getReview_list_of_recipe(recipe_id: int, page: int, page_size: int, db:Session):
        query = db.query(Review).filter(Review.recipe_id == recipe_id)
        total = query.count()
        reviews = query.offset((page -1) * page_size).limit(page_size).all()
        if reviews is None:
            return None
        return {
            "items": reviews,
            "page": page,
            "page_size": page_size,
            "total": total
        }