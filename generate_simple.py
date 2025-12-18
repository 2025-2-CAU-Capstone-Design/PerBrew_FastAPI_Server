from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import sys
import os
import uuid
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.models.user import User, UserPreference
    from app.models.bean import CoffeeBean
    from app.models.machine import Machine, BrewPhaseEnum
    from app.models.recipe import Recipe, PouringStep, TechniqueEnum
    from app.models.brew_log import BrewLog
    from app.core.database import Session as SessionLocal, init_db
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    raise

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


from sqlalchemy import Subquery

def create_mock_recipes(db: Session):

    db.commit()

    # --- Recreate beans ---

    recipes = []

    recipe_name = f"sim"

    temperature = 90
    grind_level = 85
    second_water = 125
    third_water = 75

    recipe = Recipe(
        recipe_name=recipe_name,
        user_id="test",
        bean_id=1,
        seed=True,
        is_public=True,
        dose_g=16.0,
        water_temperature_c=temperature,
        total_water_g=260.0,
        total_brew_time_s=180.0,
        brew_ratio=1 / 14.444,
        grind_level=grind_level,
        grind_microns=350,
        rinsing=True,
        source="Mock Seed Data",
    )

    db.add(recipe)
    db.flush()  # Ensure recipe_id is generated

    # Create pouring steps
    pouring_steps = [
        PouringStep(recipe_id=recipe.recipe_id, step_number=1, water_g=60.0, pour_time_s=0.0),
    ]
    for step in pouring_steps:
        db.add(step)

    recipes.append(recipe)

    db.commit()

    for recipe in recipes:
        db.refresh(recipe)

    print("✅ Successfully created 45 fresh V60 Pour Over recipes!")
    return recipes

def populate_mock_data():
    """Main function to populate all mock data"""
    db = SessionLocal()
    try:
        recipes = create_mock_recipes(db)
        
    except Exception as e:
        print(f"❌ Error populating mock data: {e}")
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_mock_data()