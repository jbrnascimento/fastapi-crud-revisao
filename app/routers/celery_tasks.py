
from pydantic import BaseModel, StrictInt

from fastapi import APIRouter

from app.celery_app import celery_app
from app.tasks import somar


router = APIRouter(
    prefix="/background-tasks",
    tags=["Tarefas em Segundo Plano"],
)


class SomaRequest(BaseModel):
    a: StrictInt
    b: StrictInt


@router.post("/somar")
def solicitar_soma(dados: SomaRequest):
    tarefa = somar.delay(dados.a, dados.b)

    return {
        "task_id": tarefa.id,
        "status": "PENDING",
    }



@router.get("/{task_id}")
def consultar_tarefa(task_id: str):
    tarefa = celery_app.AsyncResult(task_id)

    status = tarefa.status
    resultado = None
    erro = None

    if status == "SUCCESS":
        resultado = tarefa.result

    elif status == "FAILURE":
        erro = str(tarefa.result)

    return {
        "task_id": task_id,
        "status": status,
        "result": resultado,
        "error": erro,
    }
