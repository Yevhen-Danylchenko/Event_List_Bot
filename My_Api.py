from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    status: str = "new"

tasks_db: List[Task] = []

@app.post("/tasks", response_model=Task)
def add_task(task: Task):
    tasks_db.append(task)
    return task

@app.get("/tasks", response_model=List[Task])
def list_tasks():
    return tasks_db

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, title: Optional[str] = None, status: Optional[str] = None):
    for task in tasks_db:
        if task.id == task_id:
            if title:
                task.title = title
            if status:
                task.status = status
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for task in tasks_db:
        if task.id == task_id:
            tasks_db.remove(task)
            return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")