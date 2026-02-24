# Скрипт автоматической установки Reddit Clone
# Использование: .\setup.ps1

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  REDDIT CLONE - АВТОМАТИЧЕСКАЯ УСТАНОВКА" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Проверка Python
Write-Host "[1/4] Проверка Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python не установлен!" -ForegroundColor Red
    Write-Host "Скачайте Python с https://www.python.org/" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python найден: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Создание виртуального окружения
Write-Host "[2/4] Установка зависимостей..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "  - Создание виртуального окружения..."
    python -m venv venv
}

# Активация виртуального окружения
Write-Host "  - Активирование окружения..."
& ".\venv\Scripts\Activate.ps1"

# Обновление pip
Write-Host "  - Обновление pip..."
python -m pip install --upgrade pip -q

# Установка зависимостей
Write-Host "  - Установка пакетов из requirements.txt..."
pip install -r requirements.txt -q
Write-Host "✓ Все зависимости установлены" -ForegroundColor Green
Write-Host ""

# Инициализация базы данных
Write-Host "[3/4] Инициализация базы данных..." -ForegroundColor Yellow
if (-not (Test-Path "instance")) {
    New-Item -ItemType Directory -Path "instance" -Force | Out-Null
}
python init_db.py
Write-Host "✓ База данных инициализирована" -ForegroundColor Green
Write-Host ""

# Запуск приложения
Write-Host "[4/4] Запуск приложения..." -ForegroundColor Yellow
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                  ЗАПУСК ЗАВЕРШЁН                       ║" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "║  Приложение запустится по адресу:                     ║" -ForegroundColor Cyan
Write-Host "║  🌐 http://localhost:5000                             ║" -ForegroundColor Green
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "║  Данные для входа:                                    ║" -ForegroundColor Cyan
Write-Host "║  👤 Username: admin                                   ║" -ForegroundColor Green
Write-Host "║  🔑 Password: admin123                                ║" -ForegroundColor Green
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "║  Нажмите Ctrl+C для остановки сервера                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

python run.py
