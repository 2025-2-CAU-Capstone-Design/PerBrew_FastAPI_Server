# init_db.py
from core.database import engine, Base    # ← 경로만 바꿔주면 됨!
from models import *                      # models/__init__.py에서 모든 모델 불러오게 해두기

def init_database():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")

if __name__ == "__main__":
    init_database()
