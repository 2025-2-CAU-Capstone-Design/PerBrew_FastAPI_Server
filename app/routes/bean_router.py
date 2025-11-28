from fastapi import APIRouter
#from app.controller.bean_service import BeanController
from app.schemas.bean_schema import (
    BeanCreate,
    BeanUpdate,
    BeanRead,
)

router = APIRouter()

#-----------------------------------
# Bean Registration
#-----------------------------------
@router.post("/register")
def register_bean(payload: BeanCreate):
    return None
    #return BeanController.register_bean(payload)

#-----------------------------------
# Bean List
#-----------------------------------
@router.get("/list")
def bean_list():
    return None
    #return BeanController.bean_list()

#-----------------------------------
# Bean Detail
#-----------------------------------
@router.get("/{bean_id}")
def bean_detail(bean_id: int):
    return None
    #return BeanController.bean_detail(bean_id)