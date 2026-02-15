from app.db.database import get_connection
from app.schema.schema import TaskCreate

# 🔹 ADD TASK (already used)
def add_task(task: TaskCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        INSERT INTO tasks (priority, work_needed, phone_number, email, notes, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        task.priority,
        task.work_needed,
        task.phone_number,
        task.email,
        task.notes,
        task.status
    )

    cursor.execute(query, values)
    conn.commit()
    task_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return {**task.dict(), "id": task_id}


# 🔹 GET ALL TASKS
def get_all_tasks():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return tasks


# 🔹 DELETE TASK
def delete_task_by_id(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()

    deleted = cursor.rowcount

    cursor.close()
    conn.close()

    if deleted:
        return {"message": "Task deleted"}
    return {"error": "Task not found"}


# 🔹 UPDATE TASK
def update_task_by_id(task_id: int, updated_task: TaskCreate):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        UPDATE tasks 
        SET priority=%s, work_needed=%s, phone_number=%s, email=%s, notes=%s, status=%s
        WHERE id=%s
    """

    values = (
        updated_task.priority,
        updated_task.work_needed,
        updated_task.phone_number,
        updated_task.email,
        updated_task.notes,
        updated_task.status,
        task_id
    )

    cursor.execute(query, values)
    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        return {"error": "Task not found"}

    cursor.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
    updated = cursor.fetchone()

    cursor.close()
    conn.close()

    return updated