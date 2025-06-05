:: bat-файл для запуска скрипта main.py
@echo off
python main.py
if errorlevel 1 (
    echo [!] Обнаружена ошибка. Нажмите любую клавишу для выхода...
    pause
)
