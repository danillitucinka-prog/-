# 🚀 ПЕРВЫЙ ЗАПУСК - РУКОВОДСТВО

## Быстро (1 команда)

### Windows PowerShell

```powershell
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

---

## После запуска

🌐 **Откройте:** [http://localhost:5000](http://localhost:5000)

👤 **Логин:** admin

🔑 **Пароль:** admin123

---

## Если не работает

### ❌ "Python не найден"

Скачайте с [https://www.python.org/](https://www.python.org/) и установите

### ❌ Ошибка в PowerShell

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ Порт 5000 занят

Откройте `run.py` и измените `port=5001`

### ❌ Другая проблема

Попробуйте ручную установку (см. README.md)

---

Готово! Крутого тебе опыта
