from pydantic import constr, BaseModel, EmailStr, field_validator, constr
from typing import Optional
from uuid import UUID
from datetime import datetime


class User(BaseModel):
    phone: constr(strip_whitespace=True, min_length=5) | None = None
    email: Optional[EmailStr] = None
    display_name: Optional[constr(max_length=100)] = None
    city: str | None = None

class UserCreate(User):
    pass

class UserUpdate(User):
    pass

class UserRead(User):
    id: UUID
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}