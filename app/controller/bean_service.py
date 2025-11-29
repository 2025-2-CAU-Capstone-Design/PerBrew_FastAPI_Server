from sqlalchemy.orm import Session
from typing import Optional
from app.models.bean import CoffeeBean
from app.schemas.bean_schema import BeanCreate, BeanUpdate

class BeanController:
    @staticmethod
    def create(db: Session, payload: BeanCreate) -> CoffeeBean:
        new_bean = CoffeeBean(
            bean_name=payload.bean_name,
            origin=payload.origin,
            roast_level=payload.roast_level,
            roast_date=payload.roast_date,
            processing_method=payload.processing_method,
            elevation_masl=payload.elevation_masl,
            flavor_notes=payload.flavor_notes,
            description=payload.description
        )
        db.add(new_bean)
        db.commit()
        db.refresh(new_bean)
        return new_bean
    
    @staticmethod ## 리스트 반환이라 페이지네이션이 필요할 것으로 생각됨
    def get_list(db: Session, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        total = db.query(CoffeeBean).count()
        items = db.query(CoffeeBean).offset(offset).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    
    @staticmethod
    def get_detail(db: Session, bean_id: int) -> Optional[CoffeeBean]:
        return db.query(CoffeeBean).filter(CoffeeBean.bean_id == bean_id).first()
    
    @staticmethod
    def update(db: Session, bean_id: int, payload: BeanUpdate) -> Optional[CoffeeBean]:
        bean = db.query(CoffeeBean).filter(CoffeeBean.bean_id == bean_id).first()
        if not bean:
            return None
        
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(bean, key, value)
        
        db.commit()
        db.refresh(bean)
        return bean
    
    @staticmethod
    def delete(db: Session, bean_id: int) -> bool:
        bean = db.query(CoffeeBean).filter(CoffeeBean.bean_id == bean_id).first()
        if not bean: # 원두 조회 실패
            return False
        db.delete(bean)
        db.commit()
        return True