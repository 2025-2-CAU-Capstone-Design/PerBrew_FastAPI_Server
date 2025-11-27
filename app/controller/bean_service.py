from sqlalchemy.orm import Session
from app.models.bean import CoffeeBean

class BeanController:
    @staticmethod
    def get_list(db: Session, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        total = db.query(CoffeeBean).count()
        items = db.query(CoffeeBean).offset(offset).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def create(db: Session, payload):
        # 추후 구현
        pass