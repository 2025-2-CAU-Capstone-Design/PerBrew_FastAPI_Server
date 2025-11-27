from sqlalchemy.orm import Session
from app.models.recipe import Recipe
from app.schemas.recipe_schema import RecipeCreate, RecipeUpdate

class RecipeController:
    @staticmethod
    def register_recipe(payload: RecipeCreate):
        # 추후 구현
        pass

    @staticmethod
    def recipe_list(page: int, page_size: int, bean_id: int = None):
        # 추후 구현
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    @staticmethod
    def recipe_detail(recipe_id: int):
        # 추후 구현
        pass

    @staticmethod
    def update_recipe(recipe_id: int, payload: RecipeUpdate):
        # 추후 구현
        pass

    @staticmethod
    def crawl_recipe(url: str):
        # 추후 구현
        pass

    @staticmethod
    def recommend_recipe(user_id: int, limit: int):
        # 추후 구현
        return []

    @staticmethod
    def generated_recipes(user_id: int, page: int, page_size: int):
        # 추후 구현
        return {"items": [], "total": 0, "page": page, "page_size": page_size}