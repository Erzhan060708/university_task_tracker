# app/models.py

"""
Модели базы данных для AlmaU Task Tracker.
Определяет реляционную структуру: департаменты, пользователи, задачи, комментарии.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base


class Department(Base):
    """
    Департамент / кафедра университета.
    Один департамент может содержать множество сотрудников (users).
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    # Связь "один ко многим" с пользователями
    users = relationship("User", back_populates="department", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}')>"


class User(Base):
    """
    Пользователь системы (сотрудник университета).
    Может создавать задачи и оставлять комментарии.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, default="User", nullable=False)  # "Admin" или "User"
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"))

    # Связи
    department = relationship("Department", back_populates="users")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Task(Base):
    """
    Корпоративная задача, закреплённая за конкретным сотрудником.
    Статус и приоритет используются фронтендом для отображения и фильтрации.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True, default="")
    status = Column(String, nullable=False, default="New")   # New, In Progress, Done
    priority = Column(String, nullable=False, default="Medium")  # Low, Medium, High
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    # Связи
    user = relationship("User", back_populates="tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")

    
    __table_args__ = (
        Index("ix_tasks_status_priority", "status", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', priority='{self.priority}')>"


class Comment(Base):
    """
    Комментарий к задаче. Позволяет вести внутреннее обсуждение.
    При удалении задачи комментарии удаляются автоматически (каскад).
    """
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))

    # Связь с задачей
    task = relationship("Task", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, task_id={self.task_id}, text='{self.text[:30]}...')>"