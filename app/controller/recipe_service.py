from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from app.models.recipe import Recipe, PouringStep
from app.models.user import User
from app.schemas.recipe_schema import RecipeCreate, RecipeUpdate

class RecipeController:
    @staticmethod
    def register_recipe(db: Session, payload: RecipeCreate, current_user: User):
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
            grind_level=payload.grind_level,
            grind_microns=payload.grind_microns,
            rinsing=payload.rinsing,
            source=payload.source,
            url=payload.url
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
    def recipe_detail(db: Session, recipe_id: int):
        return db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()

    @staticmethod
    def update_recipe(db: Session, recipe_id: int, payload: RecipeUpdate, current_user: User):
        recipe = db.query(Recipe).filter(Recipe.recipe_id == recipe_id).first()
        if not recipe:
            return None
        
        # Ownership check (optional but recommended)
        # if recipe.user_id != current_user.user_id:
        #     return None

        # Update fields
        update_data = payload.dict(exclude_unset=True)
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
                    technique=step.get('technique')
                )
                db.add(new_step)

        db.commit()
        db.refresh(recipe)
        return recipe

    @staticmethod
    def crawl_recipe(url: str):
        # Placeholder for crawling logic
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