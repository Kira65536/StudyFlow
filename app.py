from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Task
from database import get_db
from schemas import TaskCreate, TaskUpdate, TaskPatch, TaskResponse
app = FastAPI(
    title="StudyFlow API",
    description="Backend для StudyFlow Bot",
    version="1.0.0",
)

@app.get("/")
def home():
    return {
        "message": "StudyFlow API работает"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get(
    "/tasks",
    response_model=list[TaskResponse]
)
def get_tasks(
    status: str | None = None,
    priority: str | None = None,
    db: Session = Depends(get_db)
):
        #Начинаем формировать SELECT-запрос
    statement = select(Task)
    # Если человек передал status,добавляем фильрацию по статусу
    if status is not None:
        statement = statement.where(
            Task.status == status
        )
# Если человек передал в priority, добавляем фильрацию по приоритету
    if priority is not None:
        statement = statement.where(
            Task.status == status
        )
        
    tasks = db.scalars(statement).all()
    return tasks

@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    return task

@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        status = task_data.status,
        deadline = task_data.deadline,
        completed=task_data.status == "done",
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):

    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.status = task_data.status
    task.deadline = task_data.deadline
    task.completed = task_data.status == "done"

    db.commit()
    db.refresh(task)
    return task

@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse
)

def patch_task(
    task_id: int,
    task_data: TaskPatch,
    db: Session = Depends(get_db)
):
    
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail= "Задача не найдена"
        )
    update_data = task_data.model_dump(
        exclude_unset= True
    )

    for field, value in update_data.items():
        setattr(
            task,
            field,
            value
        )

        if "status" in update_data:
            task.completed = task.status == 'done'

            db.commit()
            db.refresh(task)
            return task
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.completed = task_data.status == "done"   
    task.deadline = task_data.deadline

    db.commit()
    db.refresh(task)

    return task

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    db.delete(task)
    db.commit()

    return {
        "message": "Задача удалена"
    }