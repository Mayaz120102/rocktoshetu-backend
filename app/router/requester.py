from fastapi import APIRouter, Depends, status, HTTPException, Query
from app.router.auth import require_roles, user_dependency
from app.schemas import (
    BloodRequestResponse,
    BloodRequestCreate,
    BloodRequestUpdate,
    BloodRequestListResponse,
    RequestResponseItem,
)
from app.models import BloodRequests, DonorResponses
from app.database import db_dependency
from sqlalchemy import or_
from datetime import date
import math

router = APIRouter(
    prefix="/requester",
    tags=["requester"],
    dependencies=[Depends(require_roles("requester"))],
)


@router.post(
    "/requests",
    response_model=BloodRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    request: BloodRequestCreate, db: db_dependency, user: user_dependency
):

    request_model = BloodRequests(
        **request.model_dump(), requester_id=user.id, status="pending"
    )

    db.add(request_model)
    db.commit()
    db.refresh(request_model)

    return request_model


@router.get("/requests", response_model=BloodRequestListResponse)
def get_all_requests(
    db: db_dependency,
    user: user_dependency,
    search: str | None = Query(
        default=None, description="Search by patient name,hospital name, or request id"
    ),
    status: str | None = Query(default=None, description="Filter by request status"),
    blood_group: str | None = Query(default=None, description="Filter by blood group"),
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
    page: int = Query(default=1, ge=1, description="Pagenumber"),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of requests per page",
    ),
):

    query = db.query(BloodRequests).filter(BloodRequests.requester_id == user.id)

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

    if status:
        query = query.filter(BloodRequests.status == status)
    if blood_group:
        query = query.filter(BloodRequests.blood_group == blood_group)

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


@router.get("/requests/{request_id}", response_model=BloodRequestResponse)
def get_request_by_id(request_id: int, db: db_dependency, user: user_dependency):

    request = (
        db.query(BloodRequests)
        .filter(BloodRequests.requester_id == user.id)
        .filter(BloodRequests.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found",
        )
    return request


@router.put("/requests/{request_id}", response_model=BloodRequestResponse)
def update_request(
    request_id: int,
    request_data: BloodRequestUpdate,
    db: db_dependency,
    user: user_dependency,
):
    request = (
        db.query(BloodRequests)
        .filter(BloodRequests.requester_id == user.id)
        .filter(BloodRequests.id == request_id)
        .first()
    )
    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found",
        )

    if request.status != "pending":
        raise HTTPException(status_code=400, detail="pending request can be updated")

    update_data = request_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(request, key, value)

    db.commit()
    db.refresh(request)

    return request


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(user: user_dependency, db: db_dependency, request_id: int):

    request = (
        db.query(BloodRequests)
        .filter(BloodRequests.requester_id == user.id)
        .filter(BloodRequests.id == request_id)
        .first()
    )
    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Blood request not found",
        )

    if request.status != "pending":
        raise HTTPException(status_code=400, detail="pending request can be deleted")

    db.query(DonorResponses).filter(DonorResponses.request_id == request_id).delete()

    db.delete(request)
    db.commit()

    return None


@router.get(
    "/requests/{request_id}/responses", response_model=list[RequestResponseItem]
)
def get_request_responses(request_id: int, db: db_dependency, user: user_dependency):

    request = (
        db.query(BloodRequests)
        .filter(BloodRequests.requester_id == user.id)
        .filter(BloodRequests.id == request_id)
        .first()
    )
    if request is None:
        raise HTTPException(status_code=404, detail="blood request not found")

    return (
        db.query(DonorResponses)
        .filter(DonorResponses.request_id == request_id)
        .order_by(DonorResponses.created_at.desc())
        .all()
    )


@router.put("/requests/{request_id}/cancel", response_model=BloodRequestResponse)
def cancel_request(request_id: int, db: db_dependency, user: user_dependency):

    request = (
        db.query(BloodRequests)
        .filter(BloodRequests.requester_id == user.id)
        .filter(BloodRequests.id == request_id)
        .first()
    )

    if request is None:
        raise HTTPException(status_code=404, detail="blood request not found")

    if request.status != "pending":
        raise HTTPException(
            status_code=400, detail="only pending request can be cancelled"
        )

    request.status = "canceled"
    db.commit()
    db.refresh(request)

    return request
