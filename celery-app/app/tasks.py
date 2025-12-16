import time
from datetime import datetime
from app import celery_app
from app.database import get_db_context
from app.models import TaskResult

@celery_app.task(bind=True, name='app.tasks.cpu_intensive_task')
def cpu_intensive_task(self, duration=10):
    """Tarea CPU-bound"""
    task_id = self.request.id
    start_time = datetime.utcnow()
    
    try:
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            if not result:
                result = TaskResult(
                    task_id=task_id,
                    task_name='cpu_intensive_task',
                    status='STARTED'
                )
                db.add(result)
            else:
                result.status = 'STARTED'
            db.commit()
        
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        start = time.time()
        result_value = 0
        while time.time() - start < duration:
            result_value = fibonacci(30)
        
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - start_time).total_seconds()
        
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            result.status = 'SUCCESS'
            result.result = f'Fibonacci(30) = {result_value}, took {duration}s'
            result.duration_seconds = duration_seconds
            result.completed_at = completed_at
            db.commit()
        
        return {'status': 'success', 'result': result_value}
    
    except Exception as e:
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - start_time).total_seconds()
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            if result:
                result.status = 'FAILURE'
                result.error = str(e)
                result.duration_seconds = duration_seconds
                result.completed_at = completed_at
                db.commit()
        raise

@celery_app.task(bind=True, name='app.tasks.io_intensive_task')
def io_intensive_task(self, delay=2):
    """Tarea I/O-bound"""
    task_id = self.request.id
    start_time = datetime.utcnow()
    
    try:
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            if not result:
                result = TaskResult(
                    task_id=task_id,
                    task_name='io_intensive_task',
                    status='STARTED'
                )
                db.add(result)
            else:
                result.status = 'STARTED'
            db.commit()
        
        time.sleep(delay)
        
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - start_time).total_seconds()
        
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            result.status = 'SUCCESS'
            result.result = f'I/O completed after {delay}s'
            result.duration_seconds = duration_seconds
            result.completed_at = completed_at
            db.commit()
        
        return {'status': 'success', 'delay': delay}
    
    except Exception as e:
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - start_time).total_seconds()
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            if result:
                result.status = 'FAILURE'
                result.error = str(e)
                result.duration_seconds = duration_seconds
                result.completed_at = completed_at
                db.commit()
        raise

@celery_app.task(bind=True, name='app.tasks.quick_task')
def quick_task(self, message=''):
    """Tarea rápida"""
    task_id = self.request.id
    start_time = datetime.utcnow()
    
    try:
        with get_db_context() as db:
            result = TaskResult(
                task_id=task_id,
                task_name='quick_task',
                status='STARTED'
            )
            db.add(result)
            db.commit()
        
        time.sleep(0.5)
        
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - start_time).total_seconds()
        
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            result.status = 'SUCCESS'
            result.result = f'Quick task executed: {message}'
            result.duration_seconds = duration_seconds
            result.completed_at = completed_at
            db.commit()
        
        return {'status': 'success', 'message': message}
    
    except Exception as e:
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - start_time).total_seconds()
        with get_db_context() as db:
            result = db.query(TaskResult).filter_by(task_id=task_id).first()
            if result:
                result.status = 'FAILURE'
                result.error = str(e)
                result.duration_seconds = duration_seconds
                result.completed_at = completed_at
                db.commit()
        raise
