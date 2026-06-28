from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class PriorityEnum(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"


class StatusEnum(str, Enum):
    New = "New"
    InProgress = "In Progress"
    Done = "Done"


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: PriorityEnum = PriorityEnum.Medium
    user_id: int


class TaskUpdate(BaseModel):
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    title: Optional[str] = None
    description: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    user_id: int
    model_config = {"from_attributes": True}
