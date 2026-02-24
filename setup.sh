#!/bin/bash
# Скрипт автоматической установки Reddit Clone для Linux/Mac
# Использование: bash setup.sh

echo ""
echo "============================================================"
echo "  REDDIT CLONE - АВТОМАТИЧЕСКАЯ УСТАНОВКА"
echo "============================================================"
echo ""

# Шаг 1: Проверка Python
echo "[1/4] Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 не установлен!"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✓ Python найден: $PYTHON_VERSION"
echo ""

# Шаг 2: Установка зависимостей
echo "[2/4] Установка зависимостей..."

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "  • Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "  • Активирование окружения..."
source venv/bin/activate

# Обновление pip
echo "  • Обновление pip..."
pip install --upgrade pip -q

# Установка зависимостей
echo "  • Установка пакетов из requirements.txt..."
pip install -r requirements.txt -q
echo "✓ Все зависимости установлены"
echo ""

# Шаг 3: Инициализация базы данных
echo "[3/4] Инициализация базы данных..."
mkdir -p instance
python init_db.py
echo "✓ База данных инициализирована"
echo ""

# Шаг 4: Запуск приложения
echo "[4/4] Запуск приложения..."
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                  ЗАПУСК ЗАВЕРШЁН                       ║"
echo "║                                                        ║"
echo "║  Приложение доступно по адресу:                       ║"
echo "║  🌐 http://localhost:5000                             ║"
echo "║                                                        ║"
echo "║  Данные для входа:                                    ║"
echo "║  👤 Username: admin                                   ║"
echo "║  🔑 Password: admin123                                ║"
echo "║                                                        ║"
echo "║  Нажмите Ctrl+C для остановки сервера                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

python run.py
