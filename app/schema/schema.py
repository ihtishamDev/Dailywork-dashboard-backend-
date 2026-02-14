from pydantic import BaseModel, EmailStr
from typing import Optional

class TaskCreate(BaseModel):
    priority: str
    work_needed: str
    phone_number: str
    email: EmailStr
    notes: Optional[str] = None
    status: Optional[str] = "New Lead" 

class TaskResponse(TaskCreate):
    id: int