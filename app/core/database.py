from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

database_file = settings.DATABASE_FILE

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# SQLlite 멀티스레딩 지원
connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL,echo = True, connect_args=connect_args)

# 세션 팩토리 생성
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델들이 상속받을 Base 클래스
Base = declarative_base()

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session   