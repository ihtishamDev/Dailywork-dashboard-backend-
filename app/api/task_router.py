from fastapi import APIRouter
from app.schema.schema import TaskCreate, TaskResponse
from app.servies.task_servics import add_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/add", response_model=TaskResponse)
def create_task(task: TaskCreate):
    return add_task(task)