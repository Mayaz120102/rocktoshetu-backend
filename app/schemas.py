from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    model_validator,
    field_validator,
)
from typing import Optional, Literal
from datetime import datetime, date


class UserCreate(BaseModel):
    username: str = Field(min_length=4, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Literal["donor", "hospital", "requester"]
    phone: Optional[str] = None
    blood_group: Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]] = (
        None
    )
    city: Optional[str] = None

    @model_validator(mode="after")
    def donor_blood_group(self):
        if self.role == "donor" and self.blood_group is None:
            raise ValueError("Blood group is required")
        return self


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    phone: str | None = None
    blood_group: str | None = None
    city: str | None = None
    is_verified: bool
    is_active: bool
    is_available: bool
    created_at: datetime
    last_donation_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    blood_group: Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]] = (
        None
    )
    last_donation_date: Optional[date] = None

    @field_validator("last_donation_date")
    @classmethod
    def not_in_future(cls, v):
        if v and v > date.today():
            raise ValueError("last donation date cannot be in the future")

        return v


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)


class BloodRequestCreate(BaseModel):
    patient_name: str = Field(min_length=2, max_length=50)
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    units: int = Field(ge=1, le=10)
    urgency: Literal["normal", "urgent", "critical"]
    hospital_name: str = Field(min_length=2, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    needed_by: date

    @field_validator("needed_by")
    @classmethod
    def validate(cls, value: date):
        if value < date.today():
            raise ValueError("needed_by cannot be in the past")
        return value


class BloodRequestResponse(BaseModel):
    id: int
    requester_id: int
    patient_name: str
    blood_group: str
    units: int
    urgency: str
    hospital_name: str
    city: str
    needed_by: date
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BloodRequestUpdate(BaseModel):
    patient_name: str | None = Field(default=None, min_length=2, max_length=50)
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = None
    urgency: Literal["normal", "urgent", "critical"] | None = None
    hospital_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    needed_by: date | None = None

    @field_validator("needed_by")
    @classmethod
    def validate_needed_by(cls, value):
        if value is not None and value < date.today():
            raise ValueError("needed_by cannot be in the past")
        return value


class BloodRequestListResponse(BaseModel):
    items: list[BloodRequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DonorResponseCreate(BaseModel):
    message: str | None = Field(default=None, max_length=250)


class DonorResponseResponse(BaseModel):
    id: int
    request_id: int
    donor_id: int
    status: str
    message: str | None
    created_at: datetime
    request: BloodRequestResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class DonorResponseListResponse(BaseModel):
    items: list[DonorResponseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AvailabilityUpdate(BaseModel):
    is_available: bool


class BloodStockCreate(BaseModel):
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    units: int = Field(ge=0, le=1000)


class BloodStockUpdate(BaseModel):
    units: int = Field(ge=0, le=1000)


class BloodStockResponse(BaseModel):
    id: int
    hospital_id: int
    blood_group: str
    units: int

    model_config = ConfigDict(from_attributes=True)


class DonorInfo(BaseModel):
    id: int
    username: str
    phone: str | None
    blood_group: str | None
    city: str | None

    model_config = ConfigDict(from_attributes=True)


class RequestResponseItem(BaseModel):
    id: int
    request_id: int
    status: str
    message: str | None
    created_at: datetime
    donor: DonorInfo

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
