@echo off
setlocal ENABLEDELAYEDEXPANSION

:: === Настройки ===
set ARCHIVE_DIR=D:\Temp\PDFConvertProject_Archiv
set VERSION_FILE=version.txt

:: === Читаем версию из version.txt ===
set VERSION=unknown
for /f "usebackq delims=" %%v in ("%VERSION_FILE%") do (
    set VERSION=%%v
    goto :version_read
)
:version_read

:: === Получаем дату и время ===
for /f "tokens=1-3 delims=.-/ " %%a in ("%DATE%") do (
    set YYYY=%%c
    set MM=%%b
    set DD=%%a
)
for /f "tokens=1-2 delims=: " %%a in ("%TIME%") do (
    set HH=%%a
    set MIN=%%b
)

set HH=%HH: =0%
set MIN=%MIN: =0%

set ZIP_NAME=PDFConvert_%VERSION%_%YYYY%-%MM%-%DD%_%HH%-%MIN%.zip

:: === Создаём папку для архивов, если её нет ===
if not exist "%ARCHIVE_DIR%" (
    mkdir "%ARCHIVE_DIR%"
)

:: === Архивация через встроенный PowerShell Compress-Archive ===
powershell -NoProfile -Command ^
    "Compress-Archive -Path * -DestinationPath '%ARCHIVE_DIR%\%ZIP_NAME%' -Force"

echo ✅ Архив успешно создан: %ARCHIVE_DIR%\%ZIP_NAME%
pause
