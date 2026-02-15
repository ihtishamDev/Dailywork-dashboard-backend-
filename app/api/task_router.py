from fastapi import UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
import os
import json
import pandas as pd
from docx import Document
from app.db.database import get_connection


from fastapi import APIRouter
from app.schema.schema import TaskCreate, TaskResponse
from app.servies.task_servics import (
    add_task,
    get_all_tasks,
    delete_task_by_id,
    update_task_by_id
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/add", response_model=TaskResponse)
def create_task(task: TaskCreate):
    return add_task(task)

@router.get("/all")    
def get_tasks():
    return get_all_tasks()

@router.delete("/{task_id}")
def delete_task(task_id: int):
    return delete_task_by_id(task_id)

@router.put("/{task_id}")
def update_task(task_id: int, updated_task: TaskCreate):
    return update_task_by_id(task_id, updated_task)


# =========================================================
# ✅ Added Import / Export API (NO changes above this line)
# =========================================================



HEADERS = [
    "id", "priority", "work_needed",
    "phone_number", "email", "notes", "status"
]


@router.get("/export")
def export_tasks_csv():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, priority, work_needed, phone_number, email, notes, status FROM tasks")
    tasks = cursor.fetchall()

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=HEADERS)
    writer.writeheader()

    for task in tasks:
        writer.writerow({
            "id": task.get("id", ""),
            "priority": task.get("priority", ""),
            "work_needed": task.get("work_needed", ""),
            "phone_number": task.get("phone_number", ""),
            "email": task.get("email", ""),
            "notes": task.get("notes") or "",
            "status": task.get("status", ""),
        })

    cursor.close()
    conn.close()

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks.csv"}
    )


def read_file_upload(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext == ".json":
        content = file.file.read()
        data = json.loads(content.decode("utf-8", errors="ignore"))
        if isinstance(data, dict):
            data = data.get("tasks", [])
        if not isinstance(data, list):
            raise ValueError("❌ Invalid JSON structure")
        return data

    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file.file)
        df = df.fillna("")
        return df.to_dict(orient="records")

    elif ext == ".csv":
        df = pd.read_csv(file.file)
        df = df.fillna("")
        return df.to_dict(orient="records")

    elif ext == ".docx":
        doc = Document(file.file)
        tasks = []

        for table in doc.tables:
            headers = [cell.text.strip() for cell in table.rows[0].cells]
            for row in table.rows[1:]:
                values = [cell.text.strip() for cell in row.cells]
                tasks.append(dict(zip(headers, values)))

        if not tasks:
            raise ValueError("❌ Word file must contain a table with data")

        return tasks

    else:
        raise ValueError(f"❌ Unsupported file type: {ext}")


def normalize_task(t):
    return {
        "priority": t.get("priority") or t.get("Priority"),
        "work_needed": t.get("work_needed") or t.get("work") or t.get("Work Needed"),
        "phone_number": t.get("phone_number") or t.get("phone") or t.get("Phone"),
        "email": t.get("email") or t.get("Email"),
        "notes": t.get("notes") or t.get("Notes") or "",
        "status": t.get("status") or "New Lead",
    }


def validate_task(t):
    errors = []

    if not t.get("priority"):
        errors.append("priority is required")
    if not t.get("work_needed"):
        errors.append("work_needed is required")
    if not t.get("phone_number"):
        errors.append("phone_number is required")

    email = t.get("email")
    if email:
        email = str(email).strip()
        if "@" not in email or "." not in email:
            errors.append("email is invalid")

    return errors


def save_tasks_to_db(tasks):
    conn = get_connection()
    cursor = conn.cursor()

    total = len(tasks)
    imported = 0
    skipped = 0
    errors_preview = []

    for idx, raw in enumerate(tasks, start=1):
        t = normalize_task(raw)
        validation_errors = validate_task(t)

        if validation_errors:
            skipped += 1
            if len(errors_preview) < 10:
                errors_preview.append({
                    "row": idx,
                    "error": ", ".join(validation_errors),
                    "data": raw
                })
            continue

        try:
            query = """
                INSERT INTO tasks (priority, work_needed, phone_number, email, notes, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            values = (
                t["priority"],
                t["work_needed"],
                t["phone_number"],
                t["email"],
                t["notes"],
                t["status"],
            )

            cursor.execute(query, values)
            imported += 1

        except Exception as e:
            skipped += 1
            if len(errors_preview) < 10:
                errors_preview.append({
                    "row": idx,
                    "error": str(e),
                    "data": raw
                })

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "total": total,
        "imported": imported,
        "skipped": skipped,
        "errors_preview": errors_preview
    }


@router.post("/import")
async def import_tasks_api(file: UploadFile = File(...)):
    try:
        tasks = read_file_upload(file)

        if not tasks:
            raise HTTPException(status_code=400, detail="❌ No data found inside file")

        summary = save_tasks_to_db(tasks)

        return {"message": "✅ Import completed", "summary": summary}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))