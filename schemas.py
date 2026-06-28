from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # orm_mode емес!
    
    id: int
    username: str
    email: str
    role: str

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str | None
    priority: str
    status: str
    user_id: int
