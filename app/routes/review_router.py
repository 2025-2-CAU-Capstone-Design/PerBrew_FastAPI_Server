from fastapi import APIRouter, status, HTTPException
from app.controller.review_service import ReviewController
from app.models.user import User
from app.schemas.review_schema import (
    ReviewCreate,    # { user_id, recipe_id, rating, comment }
    Review,
    PaginatedReviews,
)


router = APIRouter()

@router.post("/", response_model=Review, status_code=status.HTTP_201_CREATED)
def recipe_evaluation(payload: ReviewCreate):
    return ReviewController.create_review(payload)

@router.get("/", response_model=PaginatedReviews, status_code=status.HTTP_200_OK)
# 반환형: { items: [Review], page: int, page_size: int, total: int | null }
def review_list(page: int = 1, page_size: int = 20):
    result = ReviewController.get_review_list(page, page_size)
    if result is None:
        raise HTTPException(status_code=500, detail="Failed to fetch reviews")
    return result

@router.get("/{recipe_id}", response_model=PaginatedReviews, status_code=status.HTTP_200_OK)
def review_list_of_recipe(recipe_id: int, page: int = 1, page_size: int = 20):
    result = ReviewController.get_review_list_of_recipe(recipe_id, page, page_size)
    if result is None:
        raise HTTPException(status_code=404, detail="No reviews found")
    return result