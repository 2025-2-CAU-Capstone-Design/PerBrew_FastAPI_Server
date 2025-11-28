import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# 1. 테스트용 인메모리 SQLite DB 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. DB 의존성 오버라이드
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 3. 테스트 실행 전후로 테이블 생성/삭제
@pytest.fixture(scope="module")
def client():
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as c:
        yield c
    
    # 테스트 종료 후 테이블 삭제
    Base.metadata.drop_all(bind=engine)