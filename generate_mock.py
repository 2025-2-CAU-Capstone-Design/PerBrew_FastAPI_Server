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
def create_mock_beans(db: Session):
    """Create 9 mock coffee beans (only if none exist yet)"""
    existing = db.query(CoffeeBean).filter(CoffeeBean.personal == False).count()
    if existing >= 9:
        print(f"ℹ️  Skipping bean creation - {existing} seed beans already exist")
        return db.query(CoffeeBean).filter(CoffeeBean.personal == False).order_by(CoffeeBean.bean_id).all()

# 1 ~ 2개만

    bean_data = [
        ("Ethiopian Yirgacheffe", "Ethiopia", "Washed", "Floral, citrus, tea-like"),
        ("Kenyan AA", "Kenya", "Washed", "Bright acidity, blackcurrant, juicy"),
        ("Colombian Supremo", "Colombia", "Washed", "Balanced, nutty, chocolate"),
        ("Brazilian Santos", "Brazil", "Natural", "Nutty, low acidity, chocolate"),
        ("Guatemalan Antigua", "Guatemala", "Washed", "Chocolate, spice, full body"),
        ("Sumatra Mandheling", "Indonesia", "Wet-hulled", "Earthy, herbal, heavy body"),
        ("Costa Rican Tarrazu", "Costa Rica", "Washed", "Clean, bright, citrus"),
        ("Panama Geisha", "Panama", "Washed", "Jasmine, bergamot, exotic"),
        ("Tanzanian Peaberry", "Tanzania", "Washed", "Winey, bright, fruity"),
    ]

    beans = []
    for name, origin, process, notes in bean_data:
        bean = CoffeeBean(
            bean_name=name,
            origin=origin,
            processing_method=process,
            roast_level="Medium",
            description=notes,
        )
        db.add(bean)
        beans.append(bean)

    db.commit()
    for bean in beans:
        db.refresh(bean)

    print("✅ Created 9 seed coffee beans")
    return beans


from sqlalchemy import Subquery

def create_mock_recipes(db: Session):
    """Delete existing seed data and create fresh 45 V60 recipes with proper bean links"""
    print("🗑️  Deleting existing seed data...")

    # --- DELETE pouring steps for seed recipes (using subquery, avoids join issue) ---
    seed_recipe_ids = db.query(Recipe.recipe_id).filter(Recipe.seed == True).subquery()
    db.query(PouringStep).filter(PouringStep.recipe_id.in_(seed_recipe_ids)).delete(synchronize_session=False)

    # --- DELETE existing seed recipes ---
    db.query(Recipe).filter(Recipe.is_public == True).delete(synchronize_session=False)

    # --- DELETE existing seed beans ---
    db.query(CoffeeBean).filter(CoffeeBean.personal == False).delete(synchronize_session=False)

    db.commit()
    print("🗑️  All existing seed recipes, steps, and beans deleted successfully")

    # --- Recreate beans ---
    beans = create_mock_beans(db)

    # --- Variation options ---
    temp_options = [85, 90, 95]              # index % 3
    grind_options = [72, 84, 96, 108, 120]    # index // 9
    second_pour_options = [150, 125, 100]     # (index % 9) % 3
    third_pour_options = [50, 75, 100]       # (index % 9) % 3

    recipes = []

    print("🔄 Creating 45 new seed recipes...")
    for index in range(45):
        bean = beans[index % 9]
        pour_variation = int(index / 3) % 3

        recipe_name = f"#{index + 1}"

        temperature = temp_options[index % 3]
        grind_level = grind_options[index // 9]
        second_water = second_pour_options[pour_variation]
        third_water = third_pour_options[pour_variation]

        recipe = Recipe(
            recipe_name=recipe_name,
            user_id="test",
            bean_id=bean.bean_id,
            seed=False,
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
            created_at=datetime.utcnow() - timedelta(days=30 + index),
        )

        db.add(recipe)
        db.flush()  # Ensure recipe_id is generated

        # Create pouring steps
        pouring_steps = [
            PouringStep(recipe_id=recipe.recipe_id, step_number=1, water_g=60.0, pour_time_s=15.0),
            PouringStep(
                recipe_id=recipe.recipe_id,
                step_number=2,
                water_g=second_water,
                pour_time_s=30.0,
                wait_time_s=30.0,
                technique=TechniqueEnum.spiral_out,
            ),
            PouringStep(
                recipe_id=recipe.recipe_id,
                step_number=3,
                water_g=third_water,
                pour_time_s=15.0,
                technique=TechniqueEnum.spiral_out,
            ),
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
        print("🔄 Starting mock data population (clean reset)...")
        recipes = create_mock_recipes(db)
        print(f"✅ Population complete - {len(recipes)} recipes in database")
        
    except Exception as e:
        print(f"❌ Error populating mock data: {e}")
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_mock_data()