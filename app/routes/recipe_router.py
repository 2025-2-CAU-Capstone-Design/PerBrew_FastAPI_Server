"""
Recipe Registration	레시피 등록	
POST	/recipe/registration	
App	to Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Body (JSON): { "name": "string", "dose_g": number, "water_g": number, "water_temperature_c": number, "grind_level": "string", "pouring_steps": [ { "step_no": integer, "water_g": number, "pour_time_s": integer, "technique": "string" } ] }	201: { "id": "string", "status": "created" }
422: { "error": "validation_error", "message": "...", "details": { "field": "..." } }


Get Recipe List	레시피 목록 조회	
GET	/recipe/recipe_list	
App to Server	
Headers: Authorization: Bearer <token>
Query: page integer(1), page_size integer(20), bean_id string(optional)	200: { "items": [ { "id": "string", "name": "string", "dose_g": number, "water_g": number, "water_temperature_c": number } ], "page": 1, "page_size": 20, "total": 0 }


Get Selected Recipe Info	선택된 레시피 상세 조회	
GET	/recipe/{recipe_id}/info	
App to	Server	
Headers: Authorization: Bearer <token>
Path params: recipe_id string	200: { "id": "string", "name": "string", "dose_g": number, "water_temperature_c": number, "grind_level": "string", "pouring_steps": [ { "step_no": integer, "water_g": number, "pour_time_s": integer, "technique": "string" } ] }
404: { "error": "recipe_not_found", "message": "..." }


Get Recommended Recipe List	사용자 맞춤 추천 레시피 목록 조회	
GET	/recipe/{user_id}/recommend	
App to	Server	
Headers: Authorization: Bearer <token>
Path params: user_id string
Query: limit integer(10)	200: { "items": [ { "id": "string", "name": "string", "score": number } ] }


Get Generated Recipe List	사용자별 생성된 레시피 목록 조회	
GET	/recipe/{user_id}/generated	
App to Server	
Headers: Authorization: Bearer <token>
Path params: user_id string
Query: page integer(1), page_size integer(20)	200: { "items": [ { "id": "string", "name": "string", "source": "generated", "created_at": "ISO-8601" } ], "page": 1, "page_size": 20, "total": 0 }


Update Recipe Element	
PATCH	/recipe/{recipe_id}/	
App to	Server	
Headers: Authorization: Bearer <token>, Content-Type: application/json
Path params: recipe_id string
Body (JSON): { "name"?: "string", "dose_g"?: number, "water_g"?: number, "water_temperature_c"?: number, "grind_level"?: "string", "pouring_steps"?: [ { "step_no": integer, "water_g": number, "pour_time_s": integer, "technique": "string" } ] }	200: { "id": "string", "status": "updated" }
404: { "error": "recipe_not_found", "message": "..." }


Crawling Recipe		
GET	/recipe/crawling/	
App to	ETCs	Query: url string
Example: /recipe/crawling/?url=https://example.com/post	200: { "recipe": { "name": "string", "dose_g": number, "water_g": number, "water_temperature_c": number, "pouring_steps": [ { "step_no": integer, "water_g": number, "pour_time_s": integer, "technique": "string" } ] } }
422: { "error": "parse_failed", "message": "..." }


"""


from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.controller.recipe_service import RecipeController
from app.schemas.recipe_schema import (
    RecipeCreate,
    RecipeRead,
    RecipeListItem,
    RecipeUpdate,
    PaginatedRecipes,
)

router = APIRouter()

# 레시피 생성
@router.post("/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    created = RecipeController.register_recipe(db, payload, current_user)
    if not created:
        raise HTTPException(status_code=500, detail="failed_to_create_recipe")
    return created

# 레시피 목록 조회
@router.get("/", response_model=PaginatedRecipes, status_code=status.HTTP_200_OK)
def list_recipes(
    page: int = Query(1, ge=1), 
    page_size: int = Query(20, ge=1, le=100), 
    bean_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    result = RecipeController.recipe_list(db, page, page_size, bean_id)
    if result is None:
        raise HTTPException(status_code=500, detail="failed_to_fetch_recipes")
    return result


# 레시피 크롤링 - 구체적 경로이므로 /{recipe_id}보다 먼저 등록
@router.get("/crawl", status_code=status.HTTP_200_OK)
def crawl_recipe(url: str = Query(..., description="URL to crawl")):
    """URL에서 레시피를 크롤링합니다."""
    data = RecipeController.crawl_recipe(url)
    if not data:
        raise HTTPException(status_code=422, detail="parse_failed")
    return {
        "status": "success",
        "recipe_data": data,
        "message": "Recipe crawled successfully. Use POST /recipe/ to save it."
    }


# 추천 레시피 목록 - 구체적 경로이므로 /{recipe_id}보다 먼저 등록
@router.get("/recommend", response_model=List[RecipeListItem], status_code=status.HTTP_200_OK)
def recommend_recipes(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """JWT 토큰의 사용자 맞춤 추천 레시피 목록 조회"""
    items = RecipeController.recommend_recipe(db, current_user.user_id, limit)
    return items


# 생성된 레시피 목록 - 구체적 경로이므로 /{recipe_id}보다 먼저 등록
@router.get("/generated", response_model=PaginatedRecipes, status_code=status.HTTP_200_OK)
def generated_recipes(
    page: int = Query(1, ge=1), 
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """JWT 토큰의 사용자가 생성한 레시피 목록 조회"""
    result = RecipeController.generated_recipes(db, current_user.user_id, page, page_size)
    if result is None:
        raise HTTPException(status_code=404, detail="no_generated_recipes")
    return result


# 레시피 상세 조회 - 동적 경로이므로 구체적 경로들 다음에 등록
@router.get("/{recipe_id}", response_model=RecipeRead, status_code=status.HTTP_200_OK)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = RecipeController.recipe_detail(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="recipe_not_found")
    return recipe


# 레시피 편집
@router.patch("/{recipe_id}", response_model=RecipeRead, status_code=status.HTTP_200_OK)
def update_recipe(
    recipe_id: int, 
    payload: RecipeUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = RecipeController.update_recipe(db, recipe_id, payload, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="recipe_not_found")
    return updated