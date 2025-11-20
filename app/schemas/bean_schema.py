from pydantic import BaseModel

class BeanRegister(BaseModel):
    bean_id: int
    bean_name: str
    origin: str
    roast_level: int

class BeanDetail(BaseModel):
    bean_id: int
    bean_name: str
    origin: str
    roast_level: int
    flavor_note: str
