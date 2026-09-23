from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.tasks import router as tasks_router

from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.tasks import router as tasks_router
from routers.ai import router as ai_router

# =========================================================
# ПРИЛОЖЕНИЕ
# =========================================================

app = FastAPI(
    title="StudyFlow API",
    description=(
        "Backend API для StudyFlow — "
        "управление пользователями, задачами "
        "и будущими AI-функциями."
    ),
    version="1.0.0",
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(ai_router)


# =========================================================
# СИСТЕМНЫЕ ENDPOINTS
# =========================================================

@app.get(
    "/",
    tags=["System"],
)
def home():
    return {
        "name": "StudyFlow API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
)
def health():
    return {
        "status": "ok"
    }