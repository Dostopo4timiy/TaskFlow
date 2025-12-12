from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()


class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(enum.Enum):
    NEW = "new"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(
        PGEnum(TaskPriority, name="task_priority_enum"),
        nullable=False,
        default=TaskPriority.MEDIUM
    )
    status = Column(
        PGEnum(TaskStatus, name="task_status_enum"),
        nullable=False,
        default=TaskStatus.NEW
    )
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)
    error_info = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error_info": self.error_info
        }
