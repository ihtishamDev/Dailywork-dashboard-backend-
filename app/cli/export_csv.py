from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
from app.db.database import get_connection

router = APIRouter()

HEADERS = [
    "id", "priority", "work_needed",
    "phone_number", "email", "notes", "status"
]

@router.get("/export")
def export_tasks():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=HEADERS)
    writer.writeheader()

    for task in tasks:
        writer.writerow(task)

    cursor.close()
    conn.close()

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks.csv"}
    )