@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ===============================================================================
echo              🌟 ОБУЧЕНИЕ УНИВЕРСАЛЬНОЙ МОДЕЛИ
echo ===============================================================================
echo.
echo 📊 Эта модель объединяет несколько датасетов:
echo    1. DermaMNIST - 7 классов (7007+ изображений)
echo    2. PAD-UFES-20 - 6 классов (2298 изображений)  
echo    3. HAM10000 - 7 классов (10000+ изображений, опционально)
echo.
echo 🎯 ИТОГО: 14+ уникальных типов кожных заболеваний!
echo.
echo 🚀 Архитектура: EfficientNet-B4
echo ⏱️  Примерное время: 2-4 часа (зависит от датасетов)
echo 💾 Результат: models/universal_model_FINAL.pth
echo.
echo ⚠️  ВАЖНО: Убедитесь что у вас есть:
echo    - dataset/dermamnist_224.npz (обязательно!)
echo    - dataset/PAD-UFES-20/ (желательно)
echo    - dataset/HAM10000/ (опционально, для максимального охвата)
echo.
pause

echo.
echo 🔄 Активация виртуального окружения...
if exist "venv310\Scripts\activate.bat" (
    call venv310\Scripts\activate.bat
) else (
    echo ❌ Ошибка активации виртуального окружения!
    echo    Проверьте что venv310 существует.
    pause
    exit /b 1
)

echo.
echo 🚀 Запуск обучения...
echo ===============================================================================
python train_universal_model.py

echo.
echo ===============================================================================
echo ✅ Обучение завершено!
echo.
echo 📁 Проверьте результаты:
echo    - models/universal_model_FINAL.pth (финальная модель)
echo    - models/universal_class_mapping.json (маппинг классов)
echo    - results/confusion_matrix_UNIVERSAL.png (confusion matrix)
echo.
echo 🎯 Теперь можно тестировать: запустите 6_TEST_UNIVERSAL.bat
echo ===============================================================================
pause


