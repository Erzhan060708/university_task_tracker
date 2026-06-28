import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from dotenv import load_dotenv
 
load_dotenv()
 
from .database import SessionLocal, engine
from . import models, schemas
 
models.Base.metadata.create_all(bind=engine)
 
app = FastAPI(title="AlmaU Task Tracker API")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ─── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "almau-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
 
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
 
 
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
 
 
def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
 
 
# ─── DB Dependency ────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
 
# ─── FRONTEND ─────────────────────────────────────────────────────────────────
@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")
 
 
# ─── AUTH ─────────────────────────────────────────────────────────────────────
@app.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
 
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role="User",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
 
 
@app.post("/login", response_model=schemas.TokenResponse)
def login(creds: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
 
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": user}
 
 
# ─── TASKS ────────────────────────────────────────────────────────────────────
@app.get("/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Task).filter(models.Task.user_id == user_id).all()
 
 
@app.post("/tasks", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    if not db.query(models.User).filter(models.User.id == task.user_id).first():
        raise HTTPException(status_code=404, detail="Пользователь не найден")
 
    new_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority.value,
        status="New",
        user_id=task.user_id,
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
        setattr(task, field, value.value if hasattr(value, "value") else value)
 
    db.commit()
    db.refresh(task)
    return task
 
 
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, user_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id,
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена или не принадлежит пользователю")
    db.delete(task)
    db.commit()
 
 
# ─── USERS ────────────────────────────────────────────────────────────────────
@app.get("/users", response_model=List[schemas.UserResponse])
def get_users(user_id: int, db: Session = Depends(get_db)):
    """Барлық қызметкерлер (тек Admin)"""
    current_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not current_user or current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    return db.query(models.User).all()
 
 
# ─── DEPARTMENTS (күрделі ORM сұрау / complex JOIN) ──────────────────────────
@app.get("/departments")
def get_departments(db: Session = Depends(get_db)):
    """Барлық кафедраларды қайтарады"""
    depts = db.query(models.Department).all()
    return [{"id": d.id, "name": d.name} for d in depts]
 
 
@app.get("/departments/{dept_id}/users-with-tasks")
def get_department_users_with_tasks(dept_id: int, db: Session = Depends(get_db)):
    """
    Күрделі ORM сұрауы (Week 4):
    Кафедра → Қызметкерлер → Олардың тапсырмалары (JOIN: departments → users → tasks)
    """
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Кафедра табылмады")
 
    users = db.query(models.User).filter(models.User.department_id == dept_id).all()
 
    return {
        "department_id": dept.id,
        "department_name": dept.name,
        "total_users": len(users),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "total_tasks": len(u.tasks),
                "tasks": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "status": t.status,
                        "priority": t.priority,
                        "description": t.description,
                    }
                    for t in u.tasks
                ],
            }
            for u in users
        ],
    }
 
 
# ─── SEED ─────────────────────────────────────────────────────────────────────
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
                department_id=dept.id,
            )
            db.add(admin)
            db.commit()
            print("✅ Admin создан: ali@almau.kz / password123")
    except Exception as e:
        print(f"⚠️ Seed error: {e}")
    finally:
        db.close()
 
 
# ─── STATIC (ең соңында болуы керек!) ────────────────────────────────────────
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")