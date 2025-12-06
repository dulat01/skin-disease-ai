@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ============================================
echo   ПУБЛИКАЦИЯ ПРОЕКТА НА GITHUB
echo ============================================
echo.

set /p REPO_URL="Введите URL вашего репозитория (например: https://github.com/dulat01/skin-disease-ai.git): "

echo.
echo Добавляем remote...
git remote add origin %REPO_URL%

echo.
echo Переименовываем ветку в main...
git branch -M main

echo.
echo Отправляем код на GitHub...
git push -u origin main

echo.
echo ============================================
echo   ГОТОВО! Ваш проект опубликован на GitHub
echo ============================================
echo.
pause

