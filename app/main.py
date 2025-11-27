from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db 
from app.routes.user_router import router as user_router
from app.routes.bean_router  import router as bean_router
from app.routes.recipe_router import router as recipe_router
from app.routes.review_router import router as review_router
from app.routes.machine_router import router as machine_router
from app.routes.ws_router import ws_router


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


app.include_router(user_router, prefix="/usr", tags=["User"])
app.include_router(recipe_router, prefix="/recipe", tags=["Recipe"])
app.include_router(machine_router, prefix="/machine", tags=["Machine"])
app.include_router(bean_router, prefix="/bean", tags=["Bean"])
app.include_router(review_router, prefix="/review", tags=["Review"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
    
@app.get("/")
async def root():
    return {"status": "Coffee Machine API Running"}