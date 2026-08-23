from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"

class TaskUpdate(BaseModel):
    title: str
    description: str
    priority: str
    completed: bool

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    completed: bool
    model_config = {
        "from_attributes": True
    }
