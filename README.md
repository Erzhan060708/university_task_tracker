# AlmaU Task Tracker

Корпоративная система управления задачами для университета.  
Проект выполнен в рамках рубежного контроля. Реализованы аутентификация, ролевая модель (Admin/User), CRUD для задач, REST API на FastAPI, фронтенд с фильтрацией и статистикой.

## Функционал

- Регистрация и вход (email/пароль) с хешированием паролей (bcrypt)
- Роли: **Admin** (создание/удаление задач), **User** (только просмотр и изменение статуса)
- Создание, чтение, обновление (статус), удаление задач
- Фильтрация задач по статусу (All, New, In Progress, Done)
- Панель статистики (всего задач, в работе, выполнено)
- Адаптивный интерфейс в премиальном ретро-стиле

## Технологии

- **Backend:** FastAPI, SQLAlchemy, SQLite, Pydantic
- **Frontend:** HTML, CSS, JavaScript (Fetch API)
- **Security:** bcrypt для хеширования паролей
- **Деплой:** Docker / Render.com

## База данных (4 таблицы)


| Таблица | Описание | Связи |
|---------|----------|-------|
| `departments` | Кафедры университета | one-to-many → users |
| `users` | Сотрудники (Admin/User) | many-to-one → departments, one-to-many → tasks |
| `tasks` | Задачи | many-to-one → users, one-to-many → comments |
| `comments` | Комментарии к задачам | many-to-one → tasks |

## API Эндпоинты

| Метод | Эндпоинт | Описание | Тело запроса |
|-------|----------|----------|--------------|
| POST | `/register` | Регистрация | `{"username": "str", "email": "email", "password": "str"}` |
| POST | `/login` | Вход | `{"email": "email", "password": "str"}` |
| GET | `/tasks?user_id={id}` | Получить задачи пользователя | – |
| POST | `/tasks` | Создать задачу | `{"title": "str", "description": "str", "priority": "Low/Medium/High", "user_id": int}` |
| PATCH | `/tasks/{task_id}` | Обновить задачу | `{"status": "New/In Progress/Done", ...}` |
| DELETE | `/tasks/{task_id}?user_id={id}` | Удалить задачу | – |


