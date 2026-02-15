import os
import json
import argparse
import pandas as pd
from docx import Document
from app.db.database import get_connection


# -----------------------------
# Detect File Type Automatically
# -----------------------------
def read_file(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".json":
        return read_json(file_path)

    elif ext in [".xlsx", ".xls"]:
        return read_excel(file_path)

    elif ext == ".csv":
        return read_csv(file_path)

    elif ext == ".docx":
        return read_word(file_path)

    else:
        raise ValueError(f"❌ Unsupported file type: {ext}")


# -----------------------------
# Read JSON
# -----------------------------
def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = data.get("tasks", [])

    if not isinstance(data, list):
        raise ValueError("❌ Invalid JSON structure")

    return data


# -----------------------------
# Read Excel
# -----------------------------
def read_excel(file_path):
    df = pd.read_excel(file_path)
    df = df.fillna("")
    return df.to_dict(orient="records")


# -----------------------------
# Read CSV
# -----------------------------
def read_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.fillna("")
    return df.to_dict(orient="records")


# -----------------------------
# Read Word (.docx Table)
# -----------------------------
def read_word(file_path):
    doc = Document(file_path)
    tasks = []

    for table in doc.tables:
        headers = [cell.text.strip() for cell in table.rows[0].cells]

        for row in table.rows[1:]:
            values = [cell.text.strip() for cell in row.cells]
            tasks.append(dict(zip(headers, values)))

    if not tasks:
        raise ValueError("❌ Word file must contain a table with data")

    return tasks


# -----------------------------
# Normalize Keys (important)
# Allows flexible column naming
# -----------------------------
def normalize_task(t):
    return {
        "priority": t.get("priority") or t.get("Priority"),
        "work_needed": t.get("work_needed") or t.get("work") or t.get("Work Needed"),
        "phone_number": t.get("phone_number") or t.get("phone") or t.get("Phone"),
        "email": t.get("email") or t.get("Email"),
        "notes": t.get("notes") or t.get("Notes") or "",
        "status": t.get("status") or "New Lead",
    }


# -----------------------------
# Save Into Database
# -----------------------------
def save_tasks_to_db(tasks):
    conn = get_connection()
    cursor = conn.cursor()

    total = len(tasks)
    imported = 0
    skipped = 0
    reasons = []

    for raw in tasks:
        t = normalize_task(raw)

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
            reasons.append(str(e))

    conn.commit()
    cursor.close()
    conn.close()

    print("\n📊 Import Summary")
    print(f"Total Records Found : {total}")
    print(f"Successfully Imported : {imported}")
    print(f"Skipped : {skipped}")

    if reasons:
        print("\nSome Errors:")
        for r in reasons[:5]:
            print(" -", r)


# -----------------------------
# Main Import Function
# -----------------------------
def import_tasks(file_path: str):
    print(f"\n📂 Processing File: {file_path}")

    if not os.path.exists(file_path):
        print("❌ File not found")
        return

    tasks = read_file(file_path)

    if not tasks:
        print("❌ No data found inside file")
        return

    print(f"✅ {len(tasks)} Records Detected")
    save_tasks_to_db(tasks)


# -----------------------------
# CLI Support
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Task Importer")
    parser.add_argument("file", help="Path to file (json/xlsx/csv/docx)")
    args = parser.parse_args()

    import_tasks(args.file)