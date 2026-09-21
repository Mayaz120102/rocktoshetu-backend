from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.router.auth import require_roles, user_dependency
from app.database import db_dependency
from app.models import BloodRequests, DonorResponses
from datetime import date
from sqlalchemy import or_
from app.schemas import (
    AvailabilityUpdate,
    BloodRequestListResponse,
    DonorResponseCreate,
    DonorResponseListResponse,
    DonorResponseResponse,
)
import math

router = APIRouter(
    prefix="/donor", tags=["donor"], dependencies=[Depends(require_roles("donor"))]
)


@router.get("/requests", response_model=BloodRequestListResponse)
def list_requests(
    db: db_dependency,
    user: user_dependency,
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


@router.post(
    "/requests/{request_id}/respond",
    response_model=DonorResponseResponse,
    status_code=201,
)
def responded_request(
    request_id: int, data: DonorResponseCreate, db: db_dependency, user: user_dependency
):

    if not user.is_available:
        raise HTTPException(status_code=400, detail="turn your availabilty")

    blood_request = (
        db.query(BloodRequests).filter(BloodRequests.id == request_id).first()
    )

    if not blood_request:
        raise HTTPException(status_code=404, detail="request not found")
    if blood_request.status != "pending":
        raise HTTPException(status_code=400, detail="request is not open")

    responded_request = (
        db.query(DonorResponses)
        .filter(
            DonorResponses.request_id == request_id, DonorResponses.donor_id == user.id
        )
        .first()
    )

    if responded_request:
        raise HTTPException(status_code=400, detail="you already responded")

    new_response = DonorResponses(
        request_id=request_id,
        donor_id=user.id,
        message=data.message,
    )

    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    return new_response


@router.get("/responses", response_model=DonorResponseListResponse)
def donor_responses(
    db: db_dependency,
    user: user_dependency,
    page: int = Query(default=1, ge=1, description="page number"),
    page_size: int = Query(
        default=10, ge=1, le=100, description="number of responses per page"
    ),
):

    query = db.query(DonorResponses).filter(DonorResponses.donor_id == user.id)

    total = query.count()
    offset = (page - 1) * page_size

    items = (
        query.order_by(DonorResponses.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = math.ceil(total / page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.delete("/responses/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_response(response_id: int, db: db_dependency, user: user_dependency):

    response = (
        db.query(DonorResponses)
        .filter(DonorResponses.id == response_id, DonorResponses.donor_id == user.id)
        .first()
    )

    if not response:
        raise HTTPException(status_code=404, detail="response not found")

    if response.request.status != "pending":
        raise HTTPException(status_code=400, detail="request is already closed")

    db.delete(response)
    db.commit()

    return None


@router.put("/availability")
def update_availability(
    data: AvailabilityUpdate, db: db_dependency, user: user_dependency
):
    user.is_available = data.is_available
    db.commit()
    return {"is_available": user.is_available}
