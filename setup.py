#!/usr/bin/env python3
"""
Скрипт автоматической установки Reddit Clone
Использование: python setup.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    """Печать заголовка"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_step(num, text):
    """Печать шага установки"""
    print(f"\n[{num}/4] {text}")
    print("-" * 50)

def print_success(text):
    """Печать успешного сообщения"""
    print(f"✓ {text}")

def print_error(text):
    """Печать ошибки"""
    print(f"✗ {text}")
    sys.exit(1)

def run_command(command, description=""):
    """Запуск команды в терминале"""
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            if description:
                print_error(f"{description}\n{result.stderr}")
            else:
                print_error(result.stderr)
        return result.stdout
    except Exception as e:
        print_error(f"Ошибка выполнения команды: {e}")

def main():
    print_header("REDDIT CLONE - АВТОМАТИЧЕСКАЯ УСТАНОВКА")
    
    # Шаг 1: Проверка Python
    print_step(1, "Проверка Python")
    try:
        python_version = run_command([sys.executable, "--version"]).strip()
        print_success(f"Python найден: {python_version}")
    except:
        print_error("Python не установлен или недоступен")
    
    # Шаг 2: Установка зависимостей
    print_step(2, "Установка зависимостей")
    
    # Создание виртуального окружения
    venv_path = Path("venv")
    if not venv_path.exists():
        print("  • Создание виртуального окружения...")
        run_command([sys.executable, "-m", "venv", "venv"], "Ошибка создания виртуального окружения")
        print_success("Виртуальное окружение создано")
    
    # Определение пути к pip
    if platform.system() == "Windows":
        pip_executable = str(venv_path / "Scripts" / "pip.exe")
        python_executable = str(venv_path / "Scripts" / "python.exe")
    else:
        pip_executable = str(venv_path / "bin" / "pip")
        python_executable = str(venv_path / "bin" / "python")
    
    # Обновление pip
    print("  • Обновление pip...")
    run_command([pip_executable, "install", "--upgrade", "pip"], "Ошибка обновления pip")
    
    # Установка зависимостей
    print("  • Установка пакетов из requirements.txt...")
    run_command([pip_executable, "install", "-r", "requirements.txt"], "Ошибка установки зависимостей")
    print_success("Все зависимости установлены")
    
    # Шаг 3: Инициализация базы данных
    print_step(3, "Инициализация базы данных")
    instance_path = Path("instance")
    instance_path.mkdir(exist_ok=True)
    run_command([python_executable, "init_db.py"], "Ошибка инициализации базы данных")
    print_success("База данных инициализирована")
    
    # Шаг 4: Запуск приложения
    print_step(4, "Запуск приложения")
    
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  ЗАПУСК ЗАВЕРШЁН".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + "  Приложение доступно по адресу:".center(58) + "║")
    print("║" + "  🌐 http://localhost:5000".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + "  Данные для входа:".center(58) + "║")
    print("║" + "  👤 Username: admin".center(58) + "║")
    print("║" + "  🔑 Password: admin123".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + "  Нажмите Ctrl+C для остановки сервера".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝\n")
    
    # Запуск приложения
    run_command([python_executable, "run.py"], "Ошибка запуска приложения")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Сервер остановлен")
        sys.exit(0)
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
