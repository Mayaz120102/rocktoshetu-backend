from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.router.auth import require_roles, user_dependency
from app.database import db_dependency
from app.models import Users, BloodRequests, DonorResponses
from datetime import date
from sqlalchemy import or_, cast, Date
from app.schemas import (
    UserResponse,
    UserListResponse,
    BloodRequestListResponse,
)
import math

router = APIRouter(
    prefix="/admin", tags=["Admin"], dependencies=[Depends(require_roles("admin"))]
)


@router.get("/users", response_model=UserListResponse)
def get_all_users(
    db: db_dependency,
    search: str | None = Query(
        default=None, description="Search by username, email, or user id"
    ),
    role: str | None = Query(
        default=None, description="donor, hospital, requester, admin"
    ),
    is_active: bool | None = Query(default=None, description="false = banned"),
    is_verified: bool | None = Query(default=None, description="Hospital verification"),
    date_from: date | None = Query(default=None, description="Joined from this date"),
    date_to: date | None = Query(default=None, description="Joined until this date"),
    sort_by: str = Query(
        default="created_at", description="created_at, username, email, or role"
    ),
    order: str = Query(default="desc", description="asc or desc"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Users per page"),
):

    query = db.query(Users)

    if search:
        if search.isdigit():
            query = query.filter(Users.id == int(search))
        else:
            query = query.filter(
                or_(
                    Users.username.ilike(f"%{search}%"),
                    Users.email.ilike(f"%{search}%"),
                )
            )

    if role:
        query = query.filter(Users.role == role)

    if is_active is not None:
        query = query.filter(Users.is_active == is_active)

    if is_verified is not None:
        query = query.filter(Users.is_verified == is_verified)

    if date_from:
        query = query.filter(cast(Users.created_at, Date) >= date_from)

    if date_to:
        query = query.filter(cast(Users.created_at, Date) <= date_to)

    valid_sort_fields = {
        "created_at": Users.created_at,
        "username": Users.username,
        "email": Users.email,
        "role": Users.role,
    }

    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=("Invalid sort_by. Choose from created_at, username, email, role"),
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


@router.put("/users/{user_id}/ban", response_model=UserResponse)
def ban_user(user_id: int, db: db_dependency, user: user_dependency):

    target = db.query(Users).filter(Users.id == user_id).first()

    if target is None:
        raise HTTPException(status_code=404, detail="user not found")

    if target.id == user.id or target.role == "admin":
        raise HTTPException(status_code=400, detail="cannot ban an admin")

    target.is_active = False
    db.commit()
    db.refresh(target)

    return target


@router.put("/users/{user_id}/unban", response_model=UserResponse)
def unban_user(user_id: int, db: db_dependency, user: user_dependency):

    target = db.query(Users).filter(Users.id == user_id).first()

    if target is None:
        raise HTTPException(status_code=404, detail="user not found")

    target.is_active = True
    db.commit()
    db.refresh(target)

    return target


@router.put("/hospitals/{user_id}/verify", response_model=UserResponse)
def verify_hospital(user_id: int, db: db_dependency):

    hospital = (
        db.query(Users)
        .filter(Users.id == user_id)
        .filter(Users.role == "hospital")
        .first()
    )

    if hospital is None:
        raise HTTPException(status_code=404, detail="hospital not found")

    hospital.is_verified = True
    db.commit()
    db.refresh(hospital)

    return hospital


@router.get("/requests", response_model=BloodRequestListResponse)
def get_all_requests(
    db: db_dependency,
    search: str | None = Query(
        default=None, description="Search by patient name,hospital name, or request id"
    ),
    status: str | None = Query(
        default=None, description="pending, fulfilled, cancelled"
    ),
    blood_group: str | None = Query(default=None, description="Filter by blood group"),
    city: str | None = Query(default=None, description="fitler by city"),
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

    query = db.query(BloodRequests)

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


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(request_id: int, db: db_dependency):

    request = db.query(BloodRequests).filter(BloodRequests.id == request_id).first()

    if request is None:
        raise HTTPException(status_code=404, detail="blood request not found")

    db.query(DonorResponses).filter(DonorResponses.request_id == request_id).delete()

    db.delete(request)
    db.commit()

    return None
