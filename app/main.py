from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db 
from app.routes.user_router import router as user_router
from app.routes.bean_router  import router as bean_router
from app.routes.recipe_router import router as recipe_router
from app.routes.review_router import router as review_router
from app.routes.machine_router import router as machine_router
from app.routes.ws_router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작 시 데이터베이스 초기화
    init_db()
    yield
    # 애플리케이션 종료 시 정리 작업 (필요한 경우 여기에 추가)  

app = FastAPI(
    title="Coffee Machine API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (개발 환경용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 프로덕션에서는 특정 도메인으로 제한 -> 허용할 출처 정의
    allow_credentials=True, # 쿠키/인증 등 정보 포함 요청을 허용할지
    allow_methods=["*"],    # 어떤 HTTP 메서드를 허용할지
    allow_headers=["*"],    # 어떤 헤더를 허용할지
)


app.include_router(user_router, prefix="/usr", tags=["User"])
app.include_router(recipe_router, prefix="/recipe", tags=["Recipe"])
app.include_router(machine_router, prefix="/machine", tags=["Machine"])
app.include_router(bean_router, prefix="/bean", tags=["Bean"])
app.include_router(review_router, prefix="/review", tags=["Review"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

@app.get("/")
async def root():
    return {"status": "Coffee Machine API Running"}