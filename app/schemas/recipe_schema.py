from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TechniqueEnum(str, Enum):
    center = "center"
    spiral_out = "spiral_out"
    pulse = "pulse"


class PouringStepCreate(BaseModel):
    step_number: int
    water_g: float
    pour_time_s: float
    wait_time_s: Optional[float] = None
    bloom_time_s: Optional[float] = None
    technique: Optional[TechniqueEnum] = None


class PouringStepRead(BaseModel):
    pouring_step_id: int
    recipe_id: int
    step_number: int
    water_g: float
    pour_time_s: float
    wait_time_s: Optional[float] = None
    bloom_time_s: Optional[float] = None
    technique: Optional[TechniqueEnum] = None

    class Config:
        from_attributes = True


class RecipeCreate(BaseModel):
    recipe_name: str
    bean_id: Optional[int] = None
    is_public: bool = False

    dose_g: float
    water_temperature_c: float
    total_water_g: Optional[float] = None
    total_brew_time_s: Optional[float] = None

    grind_level: Optional[str] = None
    grind_microns: Optional[int] = None

    rinsing: bool = False

    source: Optional[str] = None
    url: Optional[str] = None

    pouring_steps: List[PouringStepCreate]


class RecipeUpdate(BaseModel):
    recipe_name: Optional[str] = None
    bean_id: Optional[int] = None
    is_public: Optional[bool] = None

    dose_g: Optional[float] = None
    water_temperature_c: Optional[float] = None
    total_water_g: Optional[float] = None
    total_brew_time_s: Optional[float] = None

    grind_level: Optional[str] = None
    grind_microns: Optional[int] = None

    rinsing: Optional[bool] = None

    source: Optional[str] = None
    url: Optional[str] = None

    pouring_steps: Optional[List[PouringStepCreate]] = None


class RecipeListItem(BaseModel):
    recipe_id: int
    recipe_name: str
    bean_id: Optional[int]
    is_public: bool
    dose_g: float
    water_temperature_c: float
    total_water_g: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeRead(BaseModel):
    recipe_id: int
    recipe_name: str
    user_id: str
    bean_id: Optional[int]
    is_public: bool

    dose_g: float
    water_temperature_c: float
    total_water_g: Optional[float]
    total_brew_time_s: Optional[float]

    grind_level: Optional[str]
    grind_microns: Optional[int]

    rinsing: bool

    source: Optional[str]
    url: Optional[str]

    created_at: datetime
    updated_at: datetime

    pouring_steps: List[PouringStepRead]

    class Config:
        from_attributes = True


class PaginatedRecipes(BaseModel):
    items: List[RecipeListItem]
    page: int
    page_size: int
    total: Optional[int] = None
