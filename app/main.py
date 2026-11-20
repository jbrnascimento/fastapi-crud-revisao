
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import tasks, users, auth, celery_tasks
from app.services.exceptions import TaskNotFoundError

app = FastAPI(title="API de Tarefas")

@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request,
    exc: TaskNotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(celery_tasks.router)


@app.get("/")
def read_root():
    return {"message": "API de tarefas funcionando"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
