from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.router.auth import require_roles, user_dependency
from app.database import db_dependency
from app.models import BloodStock, BloodRequests
from datetime import date
from app.schemas import (
    BloodRequestListResponse,
    BloodRequestResponse,
    BloodStockCreate,
    BloodStockResponse,
    BloodStockUpdate,
)
import math
from sqlalchemy import or_

router = APIRouter(
    prefix="/hospital",
    tags=["hospital"],
    dependencies=[Depends(require_roles("hospital"))],
)


@router.post(
    "/stock", response_model=BloodStockResponse, status_code=status.HTTP_201_CREATED
)
def create_stock(data: BloodStockCreate, db: db_dependency, user: user_dependency):

    existing = (
        db.query(BloodStock)
        .filter(BloodStock.hospital_id == user.id)
        .filter(BloodStock.blood_group == data.blood_group)
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="already stock update it instead")

    new_stock = BloodStock(
        hospital_id=user.id,
        blood_group=data.blood_group,
        units=data.units,
    )

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    return new_stock


@router.get("/stock", response_model=list[BloodStockResponse])
def get_all_stock(db: db_dependency, user: user_dependency):

    return (
        db.query(BloodStock)
        .filter(BloodStock.hospital_id == user.id)
        .order_by(BloodStock.blood_group)
        .all()
    )


@router.put("/stock/{stock_id}", response_model=BloodStockResponse)
def update_stock(
    stock_id: int, data: BloodStockUpdate, db: db_dependency, user: user_dependency
):

    stock = (
        db.query(BloodStock)
        .filter(BloodStock.hospital_id == user.id)
        .filter(BloodStock.id == stock_id)
        .first()
    )

    if stock is None:
        raise HTTPException(status_code=404, detail="stock not found")

    stock.units = data.units

    db.commit()
    db.refresh(stock)

    return stock


@router.delete("/stock/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(stock_id: int, db: db_dependency, user: user_dependency):

    stock = (
        db.query(BloodStock)
        .filter(BloodStock.hospital_id == user.id)
        .filter(BloodStock.id == stock_id)
        .first()
    )

    if stock is None:
        raise HTTPException(status_code=404, detail="stock not found")

    db.delete(stock)
    db.commit()

    return None


@router.get("/requests", response_model=BloodRequestListResponse)
def list_requests(
    db: db_dependency,
    search: str | None = Query(
        default=None, description="Search by patient name, hospital name, or request id"
    ),
    blood_group: str | None = Query(default=None, description="Filter by blood group"),
    city: str | None = Query(default=None, description="Filter by city"),
    urgency: str | None = Query(default=None, description="Filter by urgency"),
    date_from: date | None = Query(
        default=None,
        description="Filter needed_by from this date",
    ),
    date_to: date | None = Query(
        default=None,
        description="Filter needed_by until this date",
    ),
    sort_by: str = Query(
        default="created_at",
        description="created_at, needed_by, units, or urgency",
    ),
    order: str = Query(
        default="desc",
        description="asc or desc",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of requests per page",
    ),
):

    query = db.query(BloodRequests).filter(BloodRequests.status == "pending")

    if search:
        if search.isdigit():
            query = query.filter(BloodRequests.id == int(search))
        else:
            query = query.filter(
                or_(
                    BloodRequests.patient_name.ilike(f"%{search}%"),
                    BloodRequests.hospital_name.ilike(f"%{search}%"),
                )
            )

    if blood_group:
        query = query.filter(BloodRequests.blood_group == blood_group)

    if city:
        query = query.filter(BloodRequests.city.ilike(f"%{city}%"))

    if urgency:
        query = query.filter(BloodRequests.urgency == urgency)

    if date_from:
        query = query.filter(BloodRequests.needed_by >= date_from)

    if date_to:
        query = query.filter(BloodRequests.needed_by <= date_to)

    valid_sort_fields = {
        "created_at": BloodRequests.created_at,
        "needed_by": BloodRequests.needed_by,
        "units": BloodRequests.units,
        "urgency": BloodRequests.urgency,
    }

    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid sort_by. Choose from created_at, needed_by, units, urgency"
            ),
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="order must be either asc or desc",
        )

    sort_column = valid_sort_fields[sort_by]

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()

    offset = (page - 1) * page_size

    items = query.offset(offset).limit(page_size).all()

    total_pages = math.ceil(total / page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.put("/requests/{request_id}/fulfill", response_model=BloodRequestResponse)
def request_fullfill(request_id: int, db: db_dependency, user: user_dependency):

    blood_request = (
        db.query(BloodRequests).filter(BloodRequests.id == request_id).first()
    )

    if blood_request is None:
        raise HTTPException(status_code=404, detail="request not found")

    if blood_request.status != "pending":
        raise HTTPException(status_code=400, detail="request is not open")

    stock = (
        db.query(BloodStock)
        .filter(BloodStock.hospital_id == user.id)
        .filter(BloodStock.blood_group == blood_request.blood_group)
        .first()
    )

    if stock is None or stock.units < blood_request.units:
        raise HTTPException(status_code=400, detail="not enough stock")

    stock.units -= blood_request.units
    blood_request.status = "fulfilled"

    db.commit()
    db.refresh(blood_request)

    return blood_request
