from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


class BrewPhase(str, Enum):
    idle = "idle"
    rinsing = "rinsing"
    blooming = "blooming"
    pouring = "pouring"
    done = "done"
    error = "error"


# 1) App -> Server
class BrewRequest(BaseModel):
    user_id: str
    recipe_id: int


# 2) Server -> Machine  
# Recipe 전송용 schema
class MachinePouringStep(BaseModel):
    step_number: int
    water_g: float
    pour_time_s: float
    wait_time_s: Optional[float] = None
    bloom_time_s: Optional[float] = None
    technique: Optional[str] = None



# 3) Machine -> Server
class BeanWeight(BaseModel):
    machine_id: str
    bean_weight_g: float


class AppBeanWeightPush(BaseModel):
    bean_weight_g: float
    timestamp: datetime


# 5) Machine Registration
class MachineRegisterSchema(BaseModel):
    nickname: Optional[str] = None
    ip_address: Optional[str] = None
    firmware_version: Optional[str] = None


class MachineRead(BaseModel):
    machine_id: str
    user_id: str
    nickname: Optional[str]
    ip_address: Optional[str]
    current_phase: BrewPhase
    last_brew_id: Optional[str]
    is_active: bool
    firmware_version: Optional[str]
    registered_at: datetime
    last_seen_at: datetime

    class Config:
        orm_mode = True


# 6) Brew Log 생성
class BrewResult(BaseModel):
    tds: Optional[float] = None
    temperature_c: Optional[float] = None
    notes: Optional[str] = None


class MachineBrewLog(BaseModel):
    brew_id: str
    recipe_id: Optional[int] = None
    bean_id: Optional[int] = None
    machine_id: Optional[str] = None
    result: BrewResult


# Response
class BrewAccepted(BaseModel):
    status: str
    machine_id: str
    brew_id: str


class RecipeStarted(BaseModel):
    status: str
    machine_id: str
    brew_id: str


class BrewingStatusResponse(BaseModel):
    brew_id: str
    phase: BrewPhase
    step_number: Optional[int]
    elapsed_s: int
    temperature_c: Optional[float]
    tds: Optional[float]
    progress_pct: int


class BrewingStoppedResponse(BaseModel):
    status: str
    machine_id: str
    brew_id: str


class RegistrationResponse(BaseModel):
    user_id: str
    machine_id: str
    status: str


class LogCreatedResponse(BaseModel):
    status: str
    log_id: int
