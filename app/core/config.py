import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str= os.getenv("ALGORITHM")
    DATABASE_FILE: str = os.getenv("DATABASE_FILE")
    DATABASE_URL: str = os.getenv("DATABASE_URL")    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))*24
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()