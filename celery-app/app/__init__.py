# app/__init__.py
from celery import Celery
import os

# Cargar configuración
celery_app = Celery(__name__)
celery_app.config_from_object('app.celeryconfig')

# Auto-discover tasks
celery_app.autodiscover_tasks(['app'])

@celery_app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
