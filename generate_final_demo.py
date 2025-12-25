# populate_final_demo.py
# 기존 모든 데모 레시피 강제 삭제 후, demo_syj 1개 + UI용 3개 생성

from datetime import datetime
from sqlalchemy.orm import Session
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.models.recipe import Recipe, PouringStep, TechniqueEnum
    from app.core.database import Session as SessionLocal
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    raise


def force_create_demo_recipes(db: Session):
    print("🗑️  기존 모든 데모 레시피 강제 삭제 시작...")

    # 모든 demo_syj 포함 이름 또는 seed=True 레시피 삭제
    demo_ids = db.query(Recipe.recipe_id).filter(
        (Recipe.recipe_name.ilike("%demo%")) | (Recipe.seed == True)
    ).all()
    demo_ids = [rid[0] for rid in demo_ids]

    if demo_ids:
        db.query(PouringStep).filter(PouringStep.recipe_id.in_(demo_ids)).delete(synchronize_session=False)
        db.query(Recipe).filter(Recipe.recipe_id.in_(demo_ids)).delete(synchronize_session=False)
        db.commit()
        print(f"   → {len(demo_ids)}개 기존 데모 레시피 삭제 완료")
    else:
        print("   → 삭제할 기존 데모 레시피 없음")

    print("🔄  demo_syj 1개 + UI용 3개 새로 생성 중...")

    # 1. 메인 데모: demo_syj (원본 그대로)
    recipe = Recipe(
        recipe_name="demo_syj",
        user_id="test",
        bean_id=1,
        seed=True,
        is_public=True,
        dose_g=20.0,
        water_temperature_c=90,
        total_water_g=260.0,
        total_brew_time_s=180.0,
        brew_ratio=1 / 14.444,
        grind_level=85,
        grind_microns=350,
        rinsing=True,
        source="Mock Seed Data",
    )
    db.add(recipe)
    db.flush()

    steps = [
        PouringStep(recipe_id=recipe.recipe_id, step_number=1, water_g=60.0, pour_time_s=20.0),
        PouringStep(recipe_id=recipe.recipe_id, step_number=2, water_g=125.0, pour_time_s=20.0, wait_time_s=20.0, technique=TechniqueEnum.spiral_out),
        PouringStep(recipe_id=recipe.recipe_id, step_number=3, water_g=75.0, pour_time_s=20.0, technique=TechniqueEnum.spiral_out),
    ]
    for s in steps:
        db.add(s)

    # 2~4. UI용 자연스러운 3개
    ui_variations = [
        ("Morning Light V60", 93, 80, 140, 60),
        ("Classic Balanced Pour", 90, 85, 125, 75),
        ("Evening Rich Brew", 88, 90, 110, 90),
    ]

    for name, temp, grind, second, third in ui_variations:
        recipe = Recipe(
            recipe_name=name,
            user_id="test",
            bean_id=1,
            seed=False,
            is_public=True,
            dose_g=20.0,
            water_temperature_c=temp,
            total_water_g=260.0,
            total_brew_time_s=180.0,
            brew_ratio=1 / 14.444,
            grind_level=grind,
            grind_microns=350,
            rinsing=True,
            source="Curated Recipe",
        )
        db.add(recipe)
        db.flush()

        steps = [
            PouringStep(recipe_id=recipe.recipe_id, step_number=1, water_g=60.0, pour_time_s=20.0),
            PouringStep(recipe_id=recipe.recipe_id, step_number=2, water_g=second, pour_time_s=20.0, wait_time_s=20.0, technique=TechniqueEnum.spiral_out),
            PouringStep(recipe_id=recipe.recipe_id, step_number=3, water_g=third, pour_time_s=20.0, technique=TechniqueEnum.spiral_out),
        ]
        for s in steps:
            db.add(s)

    db.commit()
    print("✅ 성공! 총 4개 레시피 생성 완료:")
    print("   - demo_syj (테스트용)")
    print("   - Morning Light V60")
    print("   - Classic Balanced Pour")
    print("   - Evening Rich Brew")


def main():
    db = SessionLocal()
    try:
        force_create_demo_recipes(db)
    except Exception as e:
        print(f"❌ 실패: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()