@echo off
REM Скрипт автоматической установки Reddit Clone для Windows CMD
REM Использование: setup.bat

chcp 65001 > nul
cls

echo.
echo ============================================================
echo   REDDIT CLONE - АВТОМАТИЧЕСКАЯ УСТАНОВКА
echo ============================================================
echo.

REM Проверка Python
echo [1/4] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python не установлен!
    echo Скачайте Python с https://www.python.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ Python найден: %PYTHON_VERSION%
echo.

REM Установка зависимостей
echo [2/4] Установка зависимостей...

if not exist "venv" (
    echo   - Создание виртуального окружения...
    python -m venv venv
)

echo   - Активирование окружения...
call venv\Scripts\activate.bat

echo   - Обновление pip...
python -m pip install --upgrade pip -q

echo   - Установка пакетов из requirements.txt...
pip install -r requirements.txt -q
echo ✓ Все зависимости установлены
echo.

REM Инициализация базы данных
echo [3/4] Инициализация базы данных...
if not exist "instance" mkdir instance
python init_db.py
echo ✓ База данных инициализирована
echo.

REM Запуск приложения
echo [4/4] Запуск приложения...
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                  ЗАПУСК ЗАВЕРШЁН                       ║
echo ║                                                        ║
echo ║  Приложение запустится по адресу:                     ║
echo ║  🌐 http://localhost:5000                             ║
echo ║                                                        ║
echo ║  Данные для входа:                                    ║
echo ║  👤 Username: admin                                   ║
echo ║  🔑 Password: admin123                                ║
echo ║                                                        ║
echo ║  Нажмите Ctrl+C для остановки сервера                ║
echo ╚════════════════════════════════════════════════════════╝
echo.

python run.py
pause
