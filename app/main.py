
"""
AlmaU Task Tracker — основной файл сервера FastAPI.
Реализует CRUD для задач, настройку CORS, автоматическое создание таблиц и сидирование тестовыми данными.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine
import models
import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AlmaU Task Tracker API",
    description="Бэкенд для управления задачами университета. Использует SQLite, SQLAlchemy, FastAPI.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    """Генератор сессий базы данных. Закрывает сессию после использования."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "Medium"   # Low, Medium, High

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    user_id: int = None

    class Config:
        orm_mode = True

@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    """
    Получить список всех задач.
    Возвращает массив задач с полями id, title, description, status, priority, user_id.
    """
    tasks = db.query(Task).all()
    return tasks

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """
    Создать новую задачу.
    Привязывает задачу к пользователю с id=1 (тестовый администратор).
    """
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        default_user = User(username="admin", role="Admin")
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        user = default_user

    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        status="New",
        user_id=user.id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Удалить задачу по её ID.
    Возвращает статус 204 No Content при успехе, иначе 404.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()
    return

@app.on_event("startup")
def seed_database():
    """
    При старте приложения проверяем, есть ли записи в таблице задач.
    Если нет, создаём тестового пользователя (если отсутствует) и несколько тестовых задач.
    """
    db = SessionLocal()
    try:
        if db.query(Task).count() > 0:
            return

        dept = db.query(models.Department).filter(models.Department.name == "Кафедра Информационных Систем").first()
        if not dept:
            dept = models.Department(name="Кафедра Информационных Систем")
            db.add(dept)
            db.commit()
            db.refresh(dept)

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(username="admin", role="Admin", department_id=dept.id)
            db.add(admin)
            db.commit()
            db.refresh(admin)

       
        tasks_data = [
            {"title": "Разработать фронтенд дашборда", "description": "Создать адаптивный интерфейс на HTML/CSS/JS", "priority": "High"},
            {"title": "Настроить бэкенд FastAPI", "description": "Реализовать эндпоинты и интеграцию с БД", "priority": "Medium"},
            {"title": "Протестировать ролевую модель", "description": "Проверить доступ Администратор/Сотрудник", "priority": "Low"},
        ]
        for t in tasks_data:
            task = Task(
                title=t["title"],
                description=t["description"],
                priority=t["priority"],
                status="New",
                user_id=admin.id
            )
            db.add(task)
        db.commit()
    finally:
        db.close()
