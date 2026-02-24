# 🌐 ПОЛНОЕ РУКОВОДСТВО: ОТ ЛОКАЛЬНОГО К ОБЛАКУ

## Содержание

1. [Локальное развертывание](#локальное-развертывание)
2. [Railway](#railway-рекомендуется)
3. [Vercel + Supabase](#vercel--supabase)
4. [Другие платформы](#другие-платформы)
5. [Troubleshooting](#troubleshooting)

---

## Локальное развертывание

### Windows PowerShell

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

### Windows CMD

```cmd
setup.bat
```

### Linux/Mac

```bash
bash setup.sh
```

### Любая ОС

```bash
python setup.py
```

**После запуска:** [http://localhost:5000](http://localhost:5000)

---

## Railway (РЕКОМЕНДУЕТСЯ)

### Преимущества

- ✅ Работает с Flask из коробки
- ✅ PostgreSQL БД включена
- ✅ Простое развертывание через GitHub
- ✅ Бесплатный кредит $5/день
- ✅ Окружение "development-friendly" (можно отлаживать)

### Процесс (5 минут)

#### Шаг 1: Подготовить GitHub

```bash
git init
git add .
git commit -m "Ready to deploy"
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push origin main
```

#### Шаг 2: Railway

1. Открыть [https://railway.app](https://railway.app)
2. Кликнуть "New Project" → "Deploy from GitHub"
3. Авторизоваться и выбрать свой репо
4. Нажать "Deploy"

#### Шаг 3: Инициализация

Railway автоматически создаёт PostgreSQL БД.

Инициализировать таблицы:

```bash
# Локально или в Railway terminal:
python init_db_production.py
```

#### Шаг 4: Готово

Railway выдаст URL приложения. Открыть в браузере.

---

## Vercel + Supabase

### Проблемы

- ❌ Vercel не поддерживает SQLite (нет файловой системы)
- ❌ Нужна внешняя БД (PostgreSQL)
- ⚠️ Сложнее чем Railway

### Но если хочешь Vercel

#### Шаг 1: Создать БД на Supabase

1. Открыть [https://supabase.com](https://supabase.com)
2. Sign Up → Create New Project
3. Дождаться инициализации
4. Settings → Database → Connection strings
5. Скопировать строку для Python (psycopg2)

#### Шаг 2: Подготовить GitHub

```bash
git init
git add .
git commit -m "Ready for Vercel"
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push origin main
```

#### Шаг 3: Развернуть на Vercel

1. Открыть [https://vercel.com/new](https://vercel.com/new)
2. "Import Git Repository"
3. Вбить URL своего GitHub репо
4. Нажать "Import"

#### Шаг 4: Environment Variables

Settings → Environment Variables, добавить:

```text
DATABASE_URL = (строка из Supabase)
SECRET_KEY = your-super-secret-key-12345
FLASK_ENV = production
```

#### Шаг 5: Deploy

Нажать "Deploy" → дождаться завершения

#### Шаг 6: Инициализировать БД

После развертывания инициализировать таблицы:

**Вариант А**: Локально с переменными Vercel

```bash
# Скачать переменные
npm install -g vercel
vercel env pull

# Инициализировать
python init_db_production.py
```

**Вариант Б**: Через Python код

```python
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    # Добавить admin юзера если нужно
```

---

## Другие платформы

### Render.com

1. [https://render.com](https://render.com) → Sign Up
2. "New Web Service"
3. Выбрать GitHub репо
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn app:app`
6. Add env: DATABASE_URL, SECRET_KEY, FLASK_ENV
7. Deploy

### Heroku (платный)

1. [https://heroku.com](https://heroku.com) → heroku login
2. `heroku create MY_APP_NAME`
3. `git push heroku main`
4. `heroku addons:create heroku-postgresql`
5. `heroku run python init_db_production.py`

### AWS/Azure (продвинутый)

Требует больше конфигурации. Смотри официальную документацию.

---

## Troubleshooting

### Проблема: "ModuleNotFoundError: No module named 'app'"

**Решение:**

- Убедиться что `app.py` в корне проекта
- Убедиться что requirements.txt установлены

### Проблема: "Database error" при доступе

**Решение:**

```bash
python init_db_production.py
```

### Проблема: "SECRET_KEY is required"

**Решение:**

Добавить в переменные окружения:

```text
SECRET_KEY=my-super-secret-key-12345
```

### Проблема: "Connection refused" к БД

Проверить DATABASE_URL в environment variables

**Решение:**

- Проверить что DATABASE_URL правильная
- Проверить что БД запущена (Railway/Supabase)
- Дождаться инициализации БД

### Проблема: "Host doesn't match"

**Решение:** Для Vercel добавить в переменные:
```
VERCEL_URL=your-vercel-domain.vercel.app
```

### Проблема: Приложение работает, но нет данных

**Решение:**
```bash
python init_db_production.py
```

---

## Продвинутое: Миграции с Alembic

Для более масштабных проектов используй Alembic:

```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## Монитор и обслуживание

### Используй Sentry для логирования ошибок:

```bash
pip install sentry-sdk
```

```python
import sentry_sdk
sentry_sdk.init("your-sentry-dsn")
```

### Используй новые Relic или DataDog для мониторинга

---

## Сравнение платформ

| Платформа | SQLite | PostgreSQL | Простота | Цена | Рекомендация |
|-----------|--------|-----------|----------|------|-------------|
| Railway | ❌ | ✅ | ⭐⭐⭐⭐ | Бесплатно | ⭐⭐⭐⭐⭐ |
| Vercel | ❌ | ✅ | ⭐⭐ | Бесплатно | ⭐⭐⭐ |
| Render | ❌ | ✅ | ⭐⭐⭐ | Бесплатно | ⭐⭐⭐ |
| Heroku | ❌ | ✅ | ⭐⭐⭐ | Платно | ⭐⭐ |
| AWS | ✅ | ✅ | ⭐ | Платно | ⭐ |

---

## 📞 Поддержка

- Railway: [https://railway.app/support](https://railway.app/support)
- Vercel: [https://vercel.com/support](https://vercel.com/support)
- Supabase: [https://supabase.com/support](https://supabase.com/support)
- Render: [https://render.com/support](https://render.com/support)

---

Готово! Теперь ты можешь развертывать приложение на облако
