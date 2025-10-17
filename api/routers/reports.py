from fastapi import APIRouter, Query
from typing import List, Dict

router = APIRouter()

@router.get("/")
def report(subject_id:int, date:str):
    # Minimal placeholder: CSV written by GUI at reports/exports/<date>.csv
    import os, csv
    path = f"reports/exports/{date}.csv"
    if not os.path.exists(path):
        return {"rows":[]}
    rows=[]
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return {"rows": rows}
