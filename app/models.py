from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    users = relationship("User", back_populates="department", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)      
    hashed_password = Column(String, nullable=False)                 
    role = Column(String, default="User", nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"))

    department = relationship("Department", back_populates="users")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True, default="")
    status = Column(String, nullable=False, default="New")
    priority = Column(String, nullable=False, default="Medium")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_tasks_status_priority", "status", "priority"),)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    task = relationship("Task", back_populates="comments")
