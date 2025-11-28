from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class BeanCreate(BaseModel):
    bean_name: str
    origin: str
    roast_level: int
    roast_date: Optional[date] = None
    processing_method: Optional[str] = None
    elevation_masl: Optional[int] = None
    flavor_notes: Optional[List[str]] = None
    description: Optional[str] = None


class BeanUpdate(BaseModel):
    bean_name: Optional[str] = None
    origin: Optional[str] = None
    roast_level: Optional[int] = None
    roast_date: Optional[date] = None
    processing_method: Optional[str] = None
    elevation_masl: Optional[int] = None
    flavor_notes: Optional[List[str]] = None
    description: Optional[str] = None


class BeanRead(BaseModel):
    bean_id: int
    bean_name: str
    origin: str
    roast_level: int
    roast_date: Optional[date] = None
    processing_method: Optional[str] = None
    elevation_masl: Optional[int] = None
    flavor_notes: Optional[List[str]] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
