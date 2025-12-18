# routers/review.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.recipe import PouringStep, Recipe
from app.models.brew_log import BrewLog as BrewLogModel
# assume you have a function that modifies recipe based on feedback
from app.models.user import User
from app.services.coffee_optimizer import modify_recipe_based_on_feedback

router = APIRouter()
ratio = [0.7,0.8,0.9,1.0,1.1,1.2,1.3]
class ReviewSubmit(BaseModel):
    brew_log_id: int
    taste: int          # 1-7
    tds: int            # 1-7
    weight: int         # 1-7
    intensity: int      # 1-7
    notes: Optional[str] = None

@router.post("/reviews")
def submit_review(
    review: ReviewSubmit,
    db: Session = Depends(get_db),
):
    brew_log = db.query(BrewLogModel).filter(
        BrewLogModel.log_id == review.brew_log_id,
    ).first()

    # Save review data to brew log
    brew_log.review_taste = ratio[review.taste]
    brew_log.review_tds = ratio[review.tds]
    brew_log.review_weight = ratio[review.weight]
    brew_log.review_intensity = review.intensity
    brew_log.review_notes = review.notes

    recipe = db.query(Recipe).filter(Recipe.recipe_id == brew_log.recipe_id).first()
    print(recipe)
    # Generate modified recipe
    new_recipe_data = modify_recipe_based_on_feedback(
        original_recipe=recipe,
        taste=review.taste,
        tds=review.tds,
        weight=review.weight,
        intensity=review.intensity,
    )
    pour_r = new_recipe_data['ratio']
    new_recipe_data.pop('ratio')
    # new_recipe_data.pop('recipe')
    new_recipe = Recipe(
        user_id="auto",
        # recipe_name=f"{brew_log.brew_id} (modified {brew_log.log_id})",
        seed=True,
        dose_g = recipe.dose_g,
        # copy all other fields + modified parameters
        **new_recipe_data

    )
    
    db.add(new_recipe)
    db.flush()  # get new_recipe.recipe_id
    pouring_steps = [
        PouringStep(recipe_id=new_recipe.recipe_id, step_number=1, water_g=60.0, pour_time_s=20.0),
        PouringStep(
            recipe_id=recipe.recipe_id,
            step_number=2,
            water_g=200*pour_r/(pour_r+1),
            pour_time_s=20.0,
            wait_time_s=20.0,
        ),
        PouringStep(
            recipe_id=recipe.recipe_id,
            step_number=3,
            water_g=200/(pour_r+1),
            pour_time_s=15.0,
        ),
    ]
    for step in pouring_steps:
        db.add(step)

    db.refresh(new_recipe)
    # Link as child
    brew_log.child_recipe_id = new_recipe.recipe_id

    db.commit()

    return {
        "message": "Review saved and new recipe generated",
        "new_recipe_id": new_recipe.recipe_id
    }