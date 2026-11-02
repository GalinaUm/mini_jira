# PROGRESS — mini-jira

Обновлено: 2026-11-02

## Цель

Kanban-доска (мини-Jira) на FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL.
Сущности: `User`, `Project`, `Task`, `Comment`, участники проекта через `project_members`.

## Правила работы

- Пользователь пишет код сам, ассистент объясняет и проверяет.
- В каждом блоке кода разбирать импорты: библиотека, зачем нужна, что берём.
- Перед сжатием контекста предупредить. Состояние фиксировать в этом файле.

## Сделано

- Зависимости: `requirements.txt` содержит `pwdlib[argon2]` и `psycopg2-binary`.
- PostgreSQL `mini_jira_db` доступна, миграции применяются.
- `app/config.py`, `app/database.py` готовы.
- Модели `User`, `Project`, `Task`, `Comment`, `project_members` собираются:
  `configure_mappers()` → `mappers OK`.
- Alembic:
  - `6fa22d546d69` — начальная схема;
  - `116550f153b2` — поля Kanban для `tasks`;
  - текущая голова: `116550f153b2 (head)`;
  - `alembic check` → `No new upgrade operations detected`;
  - downgrade/upgrade проверены на пустой БД.
- `Task`: добавлены `description` и `due_date`, `assignee_id` nullable,
  `created_by_id` обязательный; FK `assignee_id` — `ON DELETE SET NULL`.
- Auth готов:
  - `pwdlib[argon2]` (Argon2id), без passlib;
  - JWT через PyJWT;
  - `POST /auth/register`, `POST /auth/login`, `GET /auth/me`;
  - `app/deps.py` — `get_current_user`;
  - `app/main.py` — FastAPI, `/health`, подключены auth/projects.
- Projects CRUD готов:
  - `POST /projects/`, `GET /projects/`, `GET /projects/{id}`,
  - `PATCH /projects/{id}`, `DELETE /projects/{id}`;
  - владелец добавляется в `project_members` при создании.
- Проверено вручную через HTTP: health, register, login, me, projects CRUD.
  Тестовые данные после проверки удалены.

## В работе

Шаг 3 — участники проекта и Kanban-задачи.

Осталось:

1. `app/schemas/task.py`.
2. Эндпоинты участников проекта (добавить/удалить/список).
3. `app/api/tasks.py`: CRUD задач.
4. `PATCH /tasks/{id}/move` — смена статуса и позиции с переиндексацией колонки.
5. Подключить роутер задач в `app/main.py`.

## Дальше по плану

1. Комментарии к задачам (`app/schemas/comment.py`, `app/api/comments.py`).
2. Тесты: pytest + httpx, минимум auth и move.
3. RBAC: роли в `project_members`, проверки ownership.
4. Refresh-токены, logout, ротация.
5. Email verification и сброс пароля.
6. Rate limiting и анти-энумерация.
7. CORS и раздача фронтенда из `frontend/dist`.

## Известные проблемы

- Нет API участников проекта — добавлять в проект пока некого, кроме владельца.
- Нет схем и роутера задач.
- Нет комментариев.
- Нет тестов; `httpx`/`pytest` не установлены.
- Нет refresh-токенов; access-токен живёт 24 часа (для продакшна later 15 минут).
- Нет RBAC и ролей.
- Нет CORS/static для фронтенда.
- `security.py` использует настройки из `config.py`; в проде `SECRET_KEY` должен приходить из secret manager.

## Как продолжить в новой сессии

1. Прочитать этот файл.
2. `git status` и `git diff` в `C:\Users\user\PycharmProjects\mini-jira`.
3. Проверить миграции:
   ```powershell
   .venv\Scripts\python.exe -m alembic current
   .venv\Scripts\python.exe -m alembic check
   ```
4. Продолжить с раздела «В работе»: схемы и API задач.
