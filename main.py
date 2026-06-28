from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import bcrypt

from .database import SessionLocal, engine
from . import models, schemas

# Абсолютті жол — app/main.py орналасқан папкадан жоғары
BASE_DIR = Path(__file__).resolve().parent.parent

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AlmaU Task Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# style.css және басқа статикалық файлдар үшін
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


@app.get("/")
def serve_frontend():
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html табылмады")
    return FileResponse(str(index_path))


@app.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role="User"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.UserResponse)
def login(user_cred: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_cred.email).first()
    if not user or not verify_password(user_cred.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    return user


@app.get("/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Task).filter(models.Task.user_id == user_id).all()


@app.post("/tasks", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == task.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    new_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        status="New",
        user_id=task.user_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.patch("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_data: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, user_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()


@app.get("/users", response_model=List[schemas.UserResponse])
def get_users(user_id: int, db: Session = Depends(get_db)):
    current_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not current_user or current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    return db.query(models.User).all()


@app.on_event("startup")
def seed_database():
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            dept = models.Department(name="Кафедра Информационных Систем")
            db.add(dept)
            db.commit()
            db.refresh(dept)
            admin = models.User(
                username="Али",
                email="ali@almau.kz",
                hashed_password=hash_password("password123"),
                role="Admin",
                department_id=dept.id
            )
            db.add(admin)
            db.commit()
            print("✅ Admin создан: ali@almau.kz / password123")
    except Exception as e:
        print(f"⚠️ Seed қатесі: {e}")
    finally:
        db.close()
