from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
from app.models.recipe import Recipe, PouringStep
from app.models.user import User
from app.schemas.recipe_schema import RecipeCreate, RecipeUpdate

# OpenAI 헬퍼 함수 import
try:
    from app.utils.openai_helper import (
        scrape_website,
        extract_recipe_from_html,
        generate_recipe_from_description,
        extract_recipe_from_description
    )
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class RecipeController:
    @staticmethod
    def register_recipe(db: Session, payload: RecipeCreate, current_user: User) -> Recipe:
        # Create Recipe
        new_recipe = Recipe(            
            recipe_name=payload.recipe_name,
            user_id=current_user.user_id,
            bean_id=payload.bean_id,
            is_public=payload.is_public,
            dose_g=payload.dose_g,
            water_temperature_c=payload.water_temperature_c,
            total_water_g=payload.total_water_g,
            total_brew_time_s=payload.total_brew_time_s,
            brew_ratio=payload.brew_ratio,
            grind_level=payload.grind_level,
            grind_microns=payload.grind_microns,
            rinsing=payload.rinsing,
            source=payload.source,
            url=payload.url,
            seed = payload.seed
        )
        db.add(new_recipe)
        db.flush() # Get recipe_id

        # Create PouringSteps
        for step in payload.pouring_steps:
            new_step = PouringStep(
                recipe_id=new_recipe.recipe_id,
                step_number=step.step_number,
                water_g=step.water_g,
                pour_time_s=step.pour_time_s,
                wait_time_s=step.wait_time_s,
                bloom_time_s=step.bloom_time_s,
                technique=step.technique
            )
            db.add(new_step)
        
        db.commit()
        db.refresh(new_recipe)
        return new_recipe

    @staticmethod
    def recipe_list(db: Session, page: int, page_size: int, bean_id: Optional[int] = None):
        query = db.query(Recipe)
        if bean_id:
            query = query.filter(Recipe.bean_id == bean_id)
        
        total = query.count()
        items = query.order_by(desc(Recipe.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total
        }

    @staticmethod
    def recipe_detail(db: Session, recipe_id: int) -> Optional[Recipe]:
        return db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()

    @staticmethod
    def update_recipe(db: Session, recipe_id: int, payload: RecipeUpdate, current_user: User) -> Optional[Recipe]:
        recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
        if not recipe:
            return None
        
        # Ownership check (optional but recommended)
        # if recipe.user_id != current_user.user_id:
        #     return None

        # Update fields
        update_data = payload.model_dump(exclude_unset=True)
        pouring_steps_data = update_data.pop('pouring_steps', None)

        for key, value in update_data.items():
            setattr(recipe, key, value)
        
        # Update PouringSteps if provided
        if pouring_steps_data is not None:
            # Delete existing steps
            db.query(PouringStep).filter(PouringStep.recipe_id == recipe_id).delete()
            # Add new steps
            for step in pouring_steps_data:
                new_step = PouringStep(
                    recipe_id=recipe.recipe_id,
                    step_number=step['step_number'],
                    water_g=step['water_g'],
                    pour_time_s=step['pour_time_s'],
                    wait_time_s=step.get('wait_time_s'),
                    bloom_time_s=step.get('bloom_time_s'),
                    technique=step.get('technique'),
                    seed=step.get('seed', False)
                )
                db.add(new_step)

        db.commit()
        db.refresh(recipe)
        return recipe

    @staticmethod
    def delete_recipe(db: Session, recipe_id: int, current_user: User) -> bool:
        recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
        if not recipe:
            return False
        
        # Ownership check (optional but recommended)
        # if recipe.user_id != current_user.user_id:
        #     return False

        db.delete(recipe)
        db.commit()
        return True
    
    @staticmethod
    def crawl_recipe(url: str) -> Optional[Dict[str, Any]]:
        """URL에서 레시피를 크롤링하고 구조화된 데이터로 반환합니다."""
        if not OPENAI_AVAILABLE:
            raise Exception("OpenAI helper not available. Check OPENAI_API_KEY configuration.")
        
        try:
            # 1. 웹페이지 HTML 가져오기
            html_content = scrape_website(url)
            
            if html_content.startswith("Error"):
                return None
            
            # 2. HTML에서 레시피 추출
            recipe_data = extract_recipe_from_html(html_content)
            
            if not recipe_data:
                return None
            
            # 3. 반환된 데이터 구조 확인 및 포맷팅
            # OpenAI가 반환한 JSON을 RecipeCreate에 맞게 변환
            formatted_recipe = {
                "recipe_name": recipe_data.get("recipe_name", "Crawled Recipe"),
                "bean_id": None,  # 크롤링된 레시피는 bean_id 없음
                "is_public": True,  # 크롤링 레시피는 공개
                "dose_g": recipe_data.get("dose_g", 15.0),
                "water_temperature_c": recipe_data.get("water_temperature_c", 93.0),
                "total_water_g": recipe_data.get("total_water_g"),
                "total_brew_time_s": recipe_data.get("total_brew_time_s"),
                "brew_ratio": recipe_data.get("brew_ratio"),
                "grind_level": recipe_data.get("grind_level"),
                "grind_microns": recipe_data.get("grind_microns"),
                "rinsing": recipe_data.get("rinsing", False),
                "source": "crawled",
                "url": url,
                "pouring_steps": recipe_data.get("pouring_steps", [])
            }
            
            return formatted_recipe
            
        except Exception as e:
            print(f"Failed to crawl recipe from {url}: {e}")
            return None

    @staticmethod
    def recommend_recipe(db: Session, user_id: str, limit: int):
        # Placeholder for recommendation logic
        return db.query(Recipe).limit(limit).all()

    @staticmethod
    def generated_recipes(db: Session, user_id: str, page: int, page_size: int):
        # Placeholder for generated recipes
        query = db.query(Recipe).filter(Recipe.user_id == user_id, Recipe.source == 'generated')
        total = query.count()
        items = query.order_by(desc(Recipe.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total
        }