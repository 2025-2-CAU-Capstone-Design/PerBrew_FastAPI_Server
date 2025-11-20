from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

# 1) App -> Server : 브루잉 요청
# { "user_id": "string", "recipe_id": "string" }
class BrewRequest(BaseModel):
    user_id: str
    recipe_id: str


# 2) Server -> Machine : 레시피 송신
class PouringStep(BaseModel):
    step_no: int
    water_g: float
    pour_time_s: int
    technique: str   # center | spiral_out | pulse


class MachineRecipeSend(BaseModel):
    recipe_id: str
    water_temperature_c: float
    dose_g: float
    grind_level: str
    pouring_steps: List[PouringStep]


# 3) Machine -> Server : 원두 무게 송신
class BeanWeight(BaseModel):
    machine_id: str
    bean_weight_g: float


# 4) Server -> App : 원두 무게 Push
class AppBeanWeightPush(BaseModel):
    bean_weight_g: float
    timestamp: str   # ISO-8601


# 5) Machine Registration (machine -> server)
# Path: /machine/{user_id}/{machine_id}
# Body: { "nickname": "string|null" }
class MachineRegisterSchema(BaseModel):
    nickname: Optional[str] = None


# 6) Machine -> Server : Create Brew Log
class BrewResult(BaseModel):
    tds: Optional[float] = None
    temperature_c: Optional[float] = None
    notes: Optional[str] = None


class MachineBrewLog(BaseModel):
    brew_id: str
    recipe_id: str
    result: BrewResult



# Response Schemas
class BrewAccepted(BaseModel):
    status: str  # "accepted"
    machine_id: str
    brew_id: str

class RecipeStarted(BaseModel):
    status: str  # "started"
    machine_id: str
    brew_id: str

class OkResponse(BaseModel):
    status: str = "ok"

class BrewPhase(str, Enum):
    idle = "idle"
    rinsing = "rinsing"
    blooming = "blooming"
    pouring = "pouring"
    done = "done"
    error = "error"

class BrewingStatusResponse(BaseModel):
    brew_id: str
    phase: BrewPhase
    step_no: Optional[int] = None
    elapsed_s: int
    temperature_c: Optional[float] = None
    tds: Optional[float] = None
    progress_pct: int

class BrewingStoppedResponse(BaseModel):
    status: str  # "stopped"
    machine_id: str
    brew_id: str

class RegistrationResponse(BaseModel):
    user_id: str
    machine_id: str
    status: str  # "registered"

class LogCreatedResponse(BaseModel):
    status: str  # "logged"
    log_id: str