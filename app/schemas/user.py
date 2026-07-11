from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.core.enums import UserRole

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole
    organization_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    fullName: str
    role: UserRole
    organizationId: UUID
    organizationName: str
