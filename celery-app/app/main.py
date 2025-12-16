from fastapi import FastAPI, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import os
import psutil

from app.database import init_db, get_db
from app.models import TaskResult
from app.tasks import cpu_intensive_task, io_intensive_task, quick_task
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="Celery", description="Testing Celery optimization patterns")

container_cpu = Gauge('container_cpu_percent', 'CPU usage percentage')
container_memory = Gauge('container_memory_bytes', 'Memory usage in bytes')
container_memory_percent = Gauge('container_memory_percent', 'Memory usage percentage')

# ✅ AQUÍ: init_db() se ejecuta cuando el servidor arranca, no al importar
@app.on_event("startup")
def startup_event():
    """Se ejecuta solo UNA VEZ cuando FastAPI inicia"""
    init_db()

@app.get("/")
def root():
    return {"message": "Celery Testing API - Alive"}

@app.post("/task/cpu")
def trigger_cpu_task(duration: int = 10):
    """Dispara tarea CPU-bound"""
    task = cpu_intensive_task.apply_async(args=[duration])
    return {
        "task_id": str(task.id),
        "task_name": "cpu_intensive_task",
        "status": "queued",
        "queue": "heavy"
    }

@app.post("/task/io")
def trigger_io_task(delay: int = 2):
    """Dispara tarea I/O-bound"""
    task = io_intensive_task.apply_async(args=[delay])
    return {
        "task_id": str(task.id),
        "task_name": "io_intensive_task",
        "status": "queued",
        "queue": "default"
    }

@app.post("/task/quick")
def trigger_quick_task(message: str = "Hello"):
    """Dispara tarea rápida"""
    task = quick_task.apply_async(args=[message])
    return {
        "task_id": str(task.id),
        "task_name": "quick_task",
        "status": "queued",
        "queue": "default"
    }

@app.post("/task/bulk")
def trigger_bulk_tasks(cpu_count: int = 5, io_count: int = 5, quick_count: int = 10):
    """Dispara muchas tareas de una vez"""
    tasks = []
    
    for i in range(quick_count):
        task = quick_task.apply_async(args=[f"Quick {i}"])
        tasks.append({"task_id": str(task.id), "type": "quick"})
    
    for i in range(cpu_count):
        task = cpu_intensive_task.apply_async(args=[5])
        tasks.append({"task_id": str(task.id), "type": "cpu"})
    
    for i in range(io_count):
        task = io_intensive_task.apply_async(args=[3])
        tasks.append({"task_id": str(task.id), "type": "io"})
    
    return {
        "total_tasks": len(tasks),
        "tasks": tasks,
        "message": "Bulk tasks queued"
    }

@app.get("/task/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Obtiene el estado de una tarea"""
    result = db.query(TaskResult).filter_by(task_id=task_id).first()
    if not result:
        return {"task_id": task_id, "status": "not_found"}
    return result.to_dict()

@app.get("/tasks/recent")
def get_recent_tasks(limit: int = 20, db: Session = Depends(get_db)):
    """Obtiene las últimas N tareas"""
    tasks = db.query(TaskResult).order_by(TaskResult.created_at.desc()).limit(limit).all()
    return {
        "count": len(tasks),
        "tasks": [t.to_dict() for t in tasks]
    }

@app.get("/tasks/stats")
def get_tasks_stats(db: Session = Depends(get_db)):
    """Estadísticas de tareas"""
    total = db.query(TaskResult).count()
    success = db.query(TaskResult).filter_by(status='SUCCESS').count()
    failed = db.query(TaskResult).filter_by(status='FAILURE').count()
    pending = db.query(TaskResult).filter_by(status='PENDING').count()
    
    from sqlalchemy import func
    avg_duration = db.query(func.avg(TaskResult.duration_seconds)).filter(
        TaskResult.status == 'SUCCESS'
    ).scalar()
    
    return {
        "total_tasks": total,
        "success": success,
        "failed": failed,
        "pending": pending,
        "avg_duration_seconds": float(avg_duration) if avg_duration else 0
    }

@app.get("/metrics")
def metrics():
    """Endpoint para Prometheus"""
    container_cpu.set(psutil.Process(os.getpid()).cpu_percent(interval=0.1))
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    container_memory.set(mem_info.rss)
    container_memory_percent.set(process.memory_percent())
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health_check():
    """Health check"""
    return {"status": "healthy"}
