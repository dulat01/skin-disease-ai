"""
🔧 НАСТРОЙКА PYTORCH ОКРУЖЕНИЯ
Установка PyTorch и зависимостей для CAS_ISIC
"""

import subprocess
import sys
import os

print("="*80)
print("🔧 НАСТРОЙКА PYTORCH ОКРУЖЕНИЯ")
print("="*80)

print("\n📦 Устанавливаю PyTorch и зависимости...")
print("⚠️ Это займёт 5-10 минут...")

# Проверяем версию Python
print(f"\nPython версия: {sys.version}")

# Устанавливаем PyTorch для CPU/DirectML (для GTX 1050)
packages = [
    "numpy<2.0",  # ВАЖНО: NumPy 2.x несовместим с PyTorch 2.0
    "torch==2.0.1",
    "torchvision==0.15.2",
    "opencv-python>=4.7.0",
    "Pillow>=8.0.0",
    "scikit-learn>=1.1",
    "matplotlib>=3.7",
    "seaborn",
    "tqdm",
    "requests"
]

print("\n📦 Список пакетов для установки:")
for pkg in packages:
    print(f"   - {pkg}")

print("\n🚀 Начинаю установку...")

for pkg in packages:
    print(f"\n📥 Устанавливаю {pkg}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
        print(f"✅ {pkg} установлен")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {pkg}: {e}")

print("\n" + "="*80)
print("✅ УСТАНОВКА ЗАВЕРШЕНА")
print("="*80)

# Проверка установки
print("\n🔍 Проверка установленных пакетов...")
try:
    import torch
    print(f"✅ PyTorch {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
    
    import torchvision
    print(f"✅ TorchVision {torchvision.__version__}")
    
    import cv2
    print(f"✅ OpenCV {cv2.__version__}")
    
    import sklearn
    print(f"✅ scikit-learn {sklearn.__version__}")
    
    print("\n🎉 Все пакеты установлены успешно!")
    
except ImportError as e:
    print(f"\n❌ Ошибка импорта: {e}")
    print("Попробуйте установить пакеты вручную")

print("\n" + "="*80)
print("📝 СЛЕДУЮЩИЕ ШАГИ:")
print("="*80)
print("\n1. Скачайте веса моделей (если ещё не скачали):")
print("   python download_cas_weights.py")
print("\n2. Адаптируйте модель под PAD-UFES-20:")
print("   python adapt_cas_model.py")
print("\n3. Обучите модель:")
print("   python train_cas_adapted.py")
print("\n" + "="*80)

