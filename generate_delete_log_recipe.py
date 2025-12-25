import sys
import os
import traceback

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.models.brew_log import BrewLog
    from app.models.recipe import Recipe, PouringStep
    from app.core.database import Session as SessionLocal
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    raise


def clear_brew_data(db):
    print("🗑️  Deleting all brew-related data...")

    # 1. PouringStep 명시적 삭제 (CASCADE 안 될 경우를 대비)
    step_count = db.query(PouringStep).delete(synchronize_session=False)
    print(f"   Deleted {step_count} pouring_steps")

    # 2. BrewLog 삭제
    brew_count = db.query(BrewLog).delete(synchronize_session=False)
    print(f"   Deleted {brew_count} brew_logs")

    # 3. Recipe 삭제
    recipe_count = db.query(Recipe).delete(synchronize_session=False)
    print(f"   Deleted {recipe_count} recipes")

    db.commit()
    print("✅ All data (recipes, pouring_steps, brew_logs) successfully deleted!")


def main():
    confirm = input("⚠️  Delete ALL recipes, pouring_steps, and brew_logs? Type YES to confirm: ")
    if confirm != "YES":
        print("❌ Cancelled.")
        return

    db = SessionLocal()
    try:
        clear_brew_data(db)
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()