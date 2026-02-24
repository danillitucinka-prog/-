# 🚀 Vercel - Быстрый гайд

## ⚠️ Важное замечание

Vercel хорош для **фронтенда** (Next.js, React), а не для полноценных Flask приложений.

**Но есть способ!** Используй **Railway** - это гораздо проще.

---

## ⭐ ЛУЧШИЙ ПУТЬ: Railway (5 минут!)

### Шаг 1

Открываешь: [https://railway.app/new](https://railway.app/new)

### Шаг 2

"Deploy from GitHub" → Выбираешь свой репо

### Шаг 3

Railway сам:

- ✅ Создаёт PostgreSQL БД
- ✅ Разворачивает приложение
- ✅ Выдаёт публичный URL

### Шаг 4

```bash
python init_db_production.py
```

### Готово

---

## Если всё же хочешь Vercel

### Требования

- ❌ SQLite НЕ работает (нет файловой системы)
- ✅ PostgreSQL работает (Supabase/PlanetScale)

### Процесс

1. **Создать БД на Supabase:**
   - [https://supabase.com](https://supabase.com)
   - Создать новый проект
   - Скопировать Connection String

1. **Развернуть на Vercel:**
   - [https://vercel.com/new](https://vercel.com/new)
   - "Import Git Repository"
   - Settings → Environment Variables
   - Добавить:

```text
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

1. **Deploy** и готово

---

## 🆘 Проблемы

**Всё падает на Vercel** → Используй Railway!

**Нужна помощь** → Смотри [DEPLOY.md](DEPLOY.md)

**Полное руководство** → [VERCEL.md](VERCEL.md)

## 🔗 Полезные ссылки

- 🚂 Railway: [https://railway.app](https://railway.app) (рекомендуется)
- 📦 Vercel: [https://vercel.com](https://vercel.com)
- 🔷 Supabase: [https://supabase.com](https://supabase.com)
