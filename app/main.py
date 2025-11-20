from fastapi import FastAPI
from app.routes.user_router import router as user_router
from app.routes.bean_router  import router as bean_router
from app.routes.recipe_router import router as recipe_router
from app.routes.review_router import router as review_router
from app.routes.machine_router import router as machine_router

app = FastAPI(
    title="Coffee Machine API",
    version="1.0.0"
)

app.include_router(user_router, prefix="/usr", tags=["User"])
app.include_router(recipe_router, prefix="/recipe", tags=["Recipe"])
app.include_router(machine_router, prefix="/machine", tags=["Machine"])
app.include_router(bean_router, prefix="/bean", tags=["Bean"])
app.include_router(review_router, prefix="/review", tags=["Review"])

@app.get("/")
async def root():
    return {"status": "Coffee Machine API Running"}