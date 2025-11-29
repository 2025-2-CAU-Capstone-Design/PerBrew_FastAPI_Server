from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.controller.bean_service import BeanController
from app.schemas.bean_schema import BeanCreate, BeanUpdate, BeanRead, PaginatedBeans

router = APIRouter()

#-----------------------------------
# Bean CRUD
#-----------------------------------
@router.post("/", response_model=BeanRead, status_code=status.HTTP_201_CREATED)
def create_bean(payload: BeanCreate, db: Session = Depends(get_db)):
    """원두 등록"""
    created = BeanController.create(db, payload)
    if not created:
        raise HTTPException(status_code=500, detail="failed_to_create_bean")
    return created


@router.get("/", response_model=PaginatedBeans, status_code=status.HTTP_200_OK)
def list_beans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """원두 목록 조회 (페이지네이션)"""
    result = BeanController.get_list(db, page, page_size)
    return result


@router.get("/{bean_id}", response_model=BeanRead, status_code=status.HTTP_200_OK)
def get_bean(bean_id: int, db: Session = Depends(get_db)):
    """원두 상세 조회"""
    bean = BeanController.get_detail(db, bean_id)
    if not bean:
        raise HTTPException(status_code=404, detail="bean_not_found")
    return bean


@router.patch("/{bean_id}", response_model=BeanRead, status_code=status.HTTP_200_OK)
def update_bean(
    bean_id: int,
    payload: BeanUpdate,
    db: Session = Depends(get_db)
):
    """원두 정보 수정"""
    updated = BeanController.update(db, bean_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="bean_not_found")
    return updated


@router.delete("/{bean_id}", status_code=status.HTTP_200_OK)
def delete_bean(bean_id: int, db: Session = Depends(get_db)):
    """원두 삭제"""
    success = BeanController.delete(db, bean_id)
    if not success:
        raise HTTPException(status_code=404, detail="bean_not_found")
    return {"status": "deleted", "bean_id": bean_id}