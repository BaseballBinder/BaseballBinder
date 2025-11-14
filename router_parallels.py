# router_parallels.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
import parsing
from models import get_db

router = APIRouter(prefix="/parallels", tags=["parallels"])


@router.post("/parse", response_model=list[schemas.ParallelParsed])
def parse_parallels(req: schemas.ParallelParseRequest):
    return parsing.parse_parallel_text(req.raw_text)


@router.post("")
def create_parallels(req: schemas.ParallelCreateRequest, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .filter(models.Product.year == req.year, models.Product.name == req.product_name)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found; create checklist first")

    for p in req.parallels:
        db.add(
            models.Parallel(
                product=product,
                name=p.name,
                print_run=p.print_run,
                exclusive=p.exclusive,
                notes=p.notes,
                raw_line=p.raw_line,
            )
        )
    db.commit()
    return {"product_id": product.id, "parallels_inserted": len(req.parallels)}
