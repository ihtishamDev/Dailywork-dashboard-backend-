import typer
from app.cli.export_csv import export_tasks_to_csv
from app.cli.import_json import import_tasks_from_json

app = typer.Typer()

@app.command()
def export(csv: str):
    export_tasks_to_csv(csv)

@app.command()
def import_json(json_file: str):
    import_tasks_from_json(json_file)

if __name__ == "__main__":
    app()