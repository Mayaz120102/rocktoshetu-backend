from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from datetime import datetime, timedelta, timezone
from typing import Annotated

from app.config import settings
from app.database import db_dependency
from app.models import Users
from app.schemas import (
    UserResponse,
    UserCreate,
    TokenResponse,
    RefreshRequest,
    UserUpdate,
    UpdatePassword,
    ResetPasswordRequest,
    ForgotPasswordRequest,
)


router = APIRouter(prefix="/auth", tags=["Auth"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oAuth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")


def authenticate_user(email, password, db):
    user = db.query(Users).filter(Users.email == email).first()

    if user is None:
        return False

    if bcrypt_context.verify(password, user.hashed_password):
        return user
    return False


def create_access_token(user_id: int, expires_delta: timedelta):
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: int, expires_delta: timedelta):
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_current_user(token: Annotated[str, Depends(oAuth2_bearer)], db: db_dependency):

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Unauthorized user")

    if payload.get("type") != "access":
        raise HTTPException(status_code=400, detail="Invalid token type")

    user = db.get(Users, user_id)

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    return user


def require_roles(*roles):
    def role_checker(current_user=Depends(get_current_user)):

        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="You dont have permission")

        if current_user.role == "hospital" and not current_user.is_verified:
            raise HTTPException(status_code=403, detail="Hospital not verified yet")

        return current_user

    return role_checker


def create_reset_token(user_id, expires_delta: timedelta = timedelta(minutes=15)):
    payload = {
        "sub": str(user_id),
        "type": "reset",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


user_dependency = Annotated[Users, Depends(get_current_user)]


@router.post("/register")
def create_user(db: db_dependency, new_user: UserCreate):

    user_model = Users(
        username=new_user.username,
        email=new_user.email,
        hashed_password=bcrypt_context.hash(new_user.password),
        role=new_user.role,
        phone=new_user.phone,
        blood_group=new_user.blood_group,
        is_verified=(new_user.role != "hospital"),
        city=new_user.city,
    )
    try:
        db.add(user_model)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

    return JSONResponse(
        status_code=201, content={"message": "user created successfully"}
    )


@router.post("/login", response_model=TokenResponse)
def user_login(
    db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):

    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    access = create_access_token(
        user.id, timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh = create_refresh_token(
        user.id, timedelta(days=settings.refresh_token_expire_days)
    )

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user,
    }


@router.post(
    "/refresh",
)
def refresh_access_token(request: RefreshRequest, db: db_dependency):

    try:
        payload = jwt.decode(
            request.refresh_token, settings.secret_key, algorithms=[settings.algorithm]
        )
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Unauthorized user")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload.get("sub"))
    user = db.query(Users).filter(Users.id == user_id).first()

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh Token")

    access = create_access_token(
        user.id, timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {"access_token": access, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def view_profile(current_user: Users = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_user(data: UserUpdate, db: db_dependency, user: user_dependency):

    update_data = data.model_dump(exclude_unset=True)

    if "last_donation_date" in update_data and user.role != "donor":
        raise HTTPException(status_code=403, detail="only donor can set")

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


@router.post("/change-password")
def change_password(
    user: user_dependency, db: db_dependency, update_password: UpdatePassword
):

    if not bcrypt_context.verify(
        update_password.current_password, user.hashed_password
    ):
        raise HTTPException(status_code=400, detail="wrong password")

    user.hashed_password = bcrypt_context.hash(update_password.new_password)

    db.commit()

    return JSONResponse(
        status_code=200, content={"message": "password updated succesfully"}
    )


@router.post("/forgot-password")
def forgot_password(password_request: ForgotPasswordRequest, db: db_dependency):

    user = db.query(Users).filter(Users.email == password_request.email).first()

    if user and user.is_active:
        token = create_reset_token(user.id)
        print(f"password reset token {user.email}: {token}")

    return {"message": "if the email exists , reset link has been sent"}


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: db_dependency):

    try:
        payload = jwt.decode(
            request.token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.get(Users, user_id)

    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.hashed_password = bcrypt_context.hash(request.new_password)

    db.commit()

    return {"message": "Password reset successfully"}
