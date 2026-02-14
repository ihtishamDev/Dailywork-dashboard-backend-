# app/servies/task_servics.py
from app.schema.schema import TaskCreate, TaskResponse

fake_db = []  # temporary list as DB

def add_task(task: TaskCreate) -> TaskResponse:
    new_id = len(fake_db) + 1
    task_dict = task.dict()
    task_dict["id"] = new_id
    fake_db.append(task_dict)
    return task_dict