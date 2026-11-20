
from app.celery_app import celery_app


@celery_app.task
def somar(a: int, b: int) -> int:
    return a + b
