# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.database import Base

class TaskResult(Base):
    __tablename__ = 'task_results'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True)
    task_name = Column(String(100))
    status = Column(String(20))  # PENDING, STARTED, SUCCESS, FAILURE
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
