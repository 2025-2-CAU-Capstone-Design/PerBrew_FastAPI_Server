from pydantic import BaseModel
from typing import Optional, List

class ReviewCreate(BaseModel):
    user_id: int
    recipe_id: int
    rating: int
    comment: str

class Review(BaseModel):
    review_id: int
    user_id: int
    recipe_id: int
    rating: int
    comment: str
    created_at: str

class PaginatedReviews(BaseModel):
    items: List[Review]
    page: int
    page_size: int
    total: Optional[int] = None