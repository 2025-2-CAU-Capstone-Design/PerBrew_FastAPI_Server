from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PouringStep(BaseModel):
    step: int
    water_g: float
    pour_time_s: float
    wait_time_s: Optional[float] = None
    bloom_time_s: Optional[float] = None
    technique: Optional[str] = None

class RecipeInfo(BaseModel):
    rinsing: Optional[bool] = False
    water_temperature_c: float
    dose_g: float
    total_brew_time_s: Optional[float] = None
    grind_level: Optional[int] = None
    grind_microns: Optional[int] = None
    pouring_steps: List[PouringStep] = []

class CoffeeInfo(BaseModel):
    origin: Optional[str] = None
    notes: Optional[List[str]] = []
    elevation_masl: Optional[int] = None
    roast_level: Optional[str] = None

class RecipeCreate(BaseModel):
    name: str
    recipe_info: RecipeInfo
    coffee_info: Optional[CoffeeInfo] = None
    source: Optional[str] = None
    url: Optional[str] = None

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    recipe_info: Optional[RecipeInfo] = None
    coffee_info: Optional[CoffeeInfo] = None
    source: Optional[str] = None
    url: Optional[str] = None


class RecipeListItem(BaseModel):
    id: int
    name: str
    dose_g: Optional[float] = None
    water_g: Optional[float] = None
    water_temperature_c: Optional[float] = None
    score: Optional[float] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class RecipeRead(BaseModel):
    id: int
    name: str
    recipe_info: RecipeInfo
    coffee_info: Optional[CoffeeInfo] = None
    source: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    class Config:
        orm_mode = True

class PaginatedRecipes(BaseModel):
    items: List[RecipeListItem]
    page: int
    page_size: int
    total: Optional[int] = None