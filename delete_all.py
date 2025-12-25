import sys
import os
import traceback

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.models.brew_log import BrewLog
    from app.models.recipe import Recipe, PouringStep
    from app.models.user import User, UserPreference
    from app.models.machine import Machine
    from app.core.database import Session as SessionLocal
except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    raise


def clear_all_data(db):
    print("🗑️  Deleting ALL data from users, machines, recipes, pouring_steps, brew_logs...")

    # 1. PouringStep (Recipe의 자식)
    step_count = db.query(PouringStep).delete(synchronize_session=False)
    print(f"   Deleted {step_count} pouring_steps")

    # 2. BrewLog
    brew_count = db.query(BrewLog).delete(synchronize_session=False)
    print(f"   Deleted {brew_count} brew_logs")

    # 3. Machine (User의 자식)
    machine_count = db.query(Machine).delete(synchronize_session=False)
    print(f"   Deleted {machine_count} machines")

    # 4. Recipe (User의 자식)
    recipe_count = db.query(Recipe).delete(synchronize_session=False)
    print(f"   Deleted {recipe_count} recipes")

    # 5. UserPreference (User 1:1)
    pref_count = db.query(UserPreference).delete(synchronize_session=False)
    print(f"   Deleted {pref_count} user_preferences")

    # 6. User (마지막 - CASCADE로 나머지 정리되지만 위에서 이미 삭제했음)
    user_count = db.query(User).delete(synchronize_session=False)
    print(f"   Deleted {user_count} users")

    db.commit()
    print("✅ All user, machine, and brew-related data successfully deleted!")


def main():
    confirm = input(
        "⚠️  WARNING: This will DELETE ALL data in the following tables:\n"
        "   - users\n"
        "   - user_preferences\n"
        "   - machines\n"
        "   - recipes\n"
        "   - pouring_steps\n"
        "   - brew_logs\n\n"
        "Type YES to confirm: "
    )
    if confirm != "YES":
        print("❌ Operation cancelled.")
        return

    db = SessionLocal()
    try:
        clear_all_data(db)
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()