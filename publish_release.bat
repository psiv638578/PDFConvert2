:: publish_release.bat
:: created: 03.06.2025 13:20
:: modified: 

@echo off
:: Настройки
set VERSION=v2.5.12
set COMMENT=Релиз PDFConvertProject %VERSION%
set REMOTE=https://github.com/USERNAME/REPOSITORY.git
set BRANCH=main

:: Проверка наличия git
where git >nul 2>nul || (
    echo Ошибка: Git не установлен или не добавлен в PATH.
    pause
    exit /b
)

:: Инициализация git, если нужно
if not exist ".git" (
    echo Инициализация репозитория...
    git init
    git remote add origin %REMOTE%
)

:: Коммит и тег
git add .
git commit -m "%COMMENT%"
git tag %VERSION%

:: Публикация
git push origin %BRANCH%
git push origin %VERSION%

echo ✅ Релиз %VERSION% успешно опубликован!
pause

:: Что делает скрипт:
::  - Проверяет, есть ли .git — и инициализирует, если нет;
::  - Добавляет все изменения;
::  - Создаёт коммит с описанием;
::  - Создаёт тег в формате vX.Y.Z;
::  - Пушит изменения и тег в GitHub.

