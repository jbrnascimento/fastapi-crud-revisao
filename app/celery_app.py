
import os

from celery import Celery


celery_app = Celery(
    "fastapi_crud_revisao",
    broker=os.getenv(
        "CELERY_BROKER_URL",
        "amqp://admin:admin123@localhost:5672//",
    ),
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    result_backend=os.getenv(
        "CELERY_RESULT_BACKEND",
        "db+postgresql://postgres:123456@localhost:5432/Treinamento",
    ),
    database_table_schemas={
        "task": "fastapi_crud",
        "group": "fastapi_crud",
    },
)
