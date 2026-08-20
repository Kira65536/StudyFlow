from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="StudyFlow API",
    description="Backend для StudyFlow Bot",
    version="1.0.0",
)

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"

class TaskUpdate(BaseModel):
    title: str
    description: str
    priority: str
    completed: bool

tasks = []
next_id = 1

@app.get("/")
def home():
    return {
        "message": "StudyFlow API работает 🚀"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail="Задача не найдена"
    )

@app.post("/tasks")
def create_task(task: TaskCreate):
    global next_id
    new_task = {
        "id": next_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "completed": False,
    }

    tasks.append(new_task)
    next_id += 1
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = updated_task.title
            task["description"] = updated_task.description
            task["priority"] = updated_task.priority
            task["completed"] = updated_task.completed
            return task

    raise HTTPException(
        status_code=404,
        detail="Задача не найдена"
    )

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            deleted_task = tasks.pop(index)
            return {
                "message": "Задача удалена",
                "task": deleted_task
            }

    raise HTTPException(
        status_code=404,
        detail="Задача не найдена"
    )