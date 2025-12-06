"""
🌟 УНИВЕРСАЛЬНАЯ МОДЕЛЬ ДЛЯ ДИАГНОСТИКИ КОЖНЫХ ЗАБОЛЕВАНИЙ
Объединяет несколько датасетов для максимального охвата заболеваний

Датасеты:
1. DermaMNIST - 7 классов (7007 train images)
2. PAD-UFES-20 - 6 классов (2298 images)  
3. (опционально) HAM10000 - 7 классов (10000+ images)

Итого: 14+ уникальных типов кожных заболеваний
"""

import os
import sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms, models
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import cv2
from datetime import datetime
from PIL import Image
from collections import Counter

# ============================================================================
# 📊 КОНФИГУРАЦИЯ
# ============================================================================

# Универсальный список классов (будет заполнен автоматически)
CLASSES = []
CLASS_MAPPING = {}
NUM_CLASSES = 0

# Параметры обучения
IMG_SIZE = 224  # Увеличиваем для лучшего качества
BATCH_SIZE = 32
EPOCHS_STAGE1 = 25
EPOCHS_STAGE2 = 40
LEARNING_RATE_STAGE1 = 0.001
LEARNING_RATE_STAGE2 = 0.0001

# Проверка устройства
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\n{'='*80}")
print(f"🖥️  УСТРОЙСТВО: {device}")
print(f"{'='*80}\n")

# ============================================================================
# 🔄 ШАГ 1: ЗАГРУЗКА И ОБЪЕДИНЕНИЕ ДАТАСЕТОВ
# ============================================================================

print(f"{'='*80}")
print(f"            🔄 ЗАГРУЗКА ДАТАСЕТОВ")
print(f"{'='*80}\n")

all_images = []
all_labels = []
all_sources = []

# -----------------------------------------------------------------------------
# 1. ЗАГРУЗКА DERMAMNIST
# -----------------------------------------------------------------------------
dermamnist_path = 'dataset/dermamnist_224.npz'
if os.path.exists(dermamnist_path):
    print(f"📂 Загрузка DermaMNIST...")
    data = np.load(dermamnist_path)
    
    train_images = data['train_images']
    train_labels = data['train_labels'].squeeze()
    val_images = data['val_images']
    val_labels = data['val_labels'].squeeze()
    
    # Объединяем train и val для максимального использования данных
    dermamnist_images = np.concatenate([train_images, val_images], axis=0)
    dermamnist_labels = np.concatenate([train_labels, val_labels], axis=0)
    
    # Маппинг классов DermaMNIST
    dermamnist_class_names = [
        'ACN',  # 0 - Acne and Rosacea
        'ADE',  # 1 - Atopic Dermatitis
        'BKL',  # 2 - Benign Keratosis
        'LPL',  # 3 - Lichen Planus
        'MEL',  # 4 - Melanoma
        'BCC',  # 5 - Basal Cell Carcinoma
        'SEK'   # 6 - Seborrheic Keratosis
    ]
    
    for img, label in zip(dermamnist_images, dermamnist_labels):
        all_images.append(img)
        all_labels.append(dermamnist_class_names[label])
        all_sources.append('DermaMNIST')
    
    print(f"   ✅ DermaMNIST: {len(dermamnist_images)} изображений, {len(dermamnist_class_names)} классов")
    print(f"      Классы: {', '.join(dermamnist_class_names)}")
else:
    print(f"   ⚠️  DermaMNIST не найден по пути: {dermamnist_path}")

# -----------------------------------------------------------------------------
# 2. ЗАГРУЗКА PAD-UFES-20
# -----------------------------------------------------------------------------
pad_metadata = 'dataset/PAD-UFES-20/metadata.csv'
pad_folders = [
    'dataset/PAD-UFES-20/imgs_part_1/imgs_part_1',
    'dataset/PAD-UFES-20/imgs_part_2/imgs_part_2',
    'dataset/PAD-UFES-20/imgs_part_3/imgs_part_3'
]

if os.path.exists(pad_metadata):
    print(f"\n📂 Загрузка PAD-UFES-20...")
    df = pd.read_csv(pad_metadata)
    
    pad_class_names = ['ACK', 'BCC_PAD', 'MEL_PAD', 'NEV', 'SCC', 'SEK_PAD']
    
    pad_count = 0
    for idx, row in df.iterrows():
        img_id = row['img_id']
        label = row['diagnostic']
        
        # Поиск изображения
        found = False
        for folder in pad_folders:
            img_path = os.path.join(folder, f"{img_id}.png")
            if os.path.exists(img_path):
                try:
                    img = cv2.imread(img_path)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                    
                    # Добавляем суффикс _PAD для избежания конфликтов
                    label_mapped = label + '_PAD' if label in ['BCC', 'MEL', 'SEK'] else label
                    
                    all_images.append(img)
                    all_labels.append(label_mapped)
                    all_sources.append('PAD-UFES-20')
                    pad_count += 1
                    found = True
                    break
                except Exception as e:
                    continue
    
    print(f"   ✅ PAD-UFES-20: {pad_count} изображений")
    print(f"      Классы: {', '.join(pad_class_names)}")
else:
    print(f"   ⚠️  PAD-UFES-20 не найден")

# -----------------------------------------------------------------------------
# 3. (ОПЦИОНАЛЬНО) ЗАГРУЗКА HAM10000
# -----------------------------------------------------------------------------
ham_metadata = 'dataset/HAM10000/HAM10000_metadata.csv'
ham_folders = [
    'dataset/HAM10000/HAM10000_images_part_1',
    'dataset/HAM10000/HAM10000_images_part_2'
]

if os.path.exists(ham_metadata):
    print(f"\n📂 Загрузка HAM10000...")
    df_ham = pd.read_csv(ham_metadata)
    
    ham_class_names = ['AKI', 'BKL_HAM', 'DF', 'MEL_HAM', 'NV', 'VASC', 'BCC_HAM']
    ham_class_mapping = {
        'akiec': 'AKI',
        'bkl': 'BKL_HAM',
        'df': 'DF',
        'mel': 'MEL_HAM',
        'nv': 'NV',
        'vasc': 'VASC',
        'bcc': 'BCC_HAM'
    }
    
    ham_count = 0
    for idx, row in df_ham.iterrows():
        img_id = row['image_id']
        dx = row['dx']
        
        if dx not in ham_class_mapping:
            continue
        
        label = ham_class_mapping[dx]
        
        # Поиск изображения
        found = False
        for folder in ham_folders:
            for ext in ['.jpg', '.jpeg', '.png']:
                img_path = os.path.join(folder, f"{img_id}{ext}")
                if os.path.exists(img_path):
                    try:
                        img = cv2.imread(img_path)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                        
                        all_images.append(img)
                        all_labels.append(label)
                        all_sources.append('HAM10000')
                        ham_count += 1
                        found = True
                        break
                    except Exception as e:
                        continue
            if found:
                break
    
    print(f"   ✅ HAM10000: {ham_count} изображений")
    print(f"      Классы: {', '.join(ham_class_names)}")
else:
    print(f"   ⚠️  HAM10000 не найден (это нормально, можно продолжить без него)")

# ============================================================================
# 📊 ШАГ 2: АНАЛИЗ ОБЪЕДИНЕННОГО ДАТАСЕТА
# ============================================================================

print(f"\n{'='*80}")
print(f"            📊 СТАТИСТИКА ОБЪЕДИНЕННОГО ДАТАСЕТА")
print(f"{'='*80}\n")

print(f"📊 ОБЩАЯ ИНФОРМАЦИЯ:")
print(f"   Всего изображений: {len(all_images)}")
print(f"   Источники: {', '.join(set(all_sources))}")

# Создание уникального списка классов
unique_classes = sorted(list(set(all_labels)))
NUM_CLASSES = len(unique_classes)
CLASSES = unique_classes

# Создание маппинга класс -> индекс
CLASS_MAPPING = {class_name: idx for idx, class_name in enumerate(CLASSES)}

print(f"\n📋 КЛАССЫ ({NUM_CLASSES} типов):")
for idx, class_name in enumerate(CLASSES):
    count = all_labels.count(class_name)
    percentage = (count / len(all_labels)) * 100
    sources = set([all_sources[i] for i, label in enumerate(all_labels) if label == class_name])
    print(f"   {idx:2d}. {class_name:15s}: {count:5d} ({percentage:5.2f}%) - {', '.join(sources)}")

# Конвертация меток в индексы
all_labels_idx = [CLASS_MAPPING[label] for label in all_labels]

# Конвертация в numpy
all_images = np.array(all_images)
all_labels_idx = np.array(all_labels_idx)
all_sources = np.array(all_sources)

print(f"\n✅ Датасет готов к обучению!")

# ============================================================================
# 🔀 ШАГ 3: РАЗДЕЛЕНИЕ НА TRAIN/VAL/TEST
# ============================================================================

print(f"\n{'='*80}")
print(f"            🔀 РАЗДЕЛЕНИЕ ДАТАСЕТА")
print(f"{'='*80}\n")

# Сначала отделяем тестовую выборку (15%)
X_temp, X_test, y_temp, y_test = train_test_split(
    all_images, all_labels_idx, test_size=0.15, random_state=42, stratify=all_labels_idx
)

# Затем из оставшихся делим на train (80%) и val (20%)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.2, random_state=42, stratify=y_temp
)

print(f"✅ Разделение завершено:")
print(f"   Train: {len(X_train)} ({len(X_train)/len(all_images)*100:.1f}%)")
print(f"   Val:   {len(X_val)} ({len(X_val)/len(all_images)*100:.1f}%)")
print(f"   Test:  {len(X_test)} ({len(X_test)/len(all_images)*100:.1f}%)")

# ============================================================================
# 🖼️ ШАГ 4: DATASET И DATALOADER
# ============================================================================

class UniversalDataset(Dataset):
    """Универсальный датасет для всех источников"""
    
    def __init__(self, images, labels, transform=None):
        self.images = images
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image = self.images[idx]
        label = self.labels[idx]
        
        # Конвертация в PIL для трансформаций
        image = Image.fromarray(image.astype('uint8'))
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

# Трансформации
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.5),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Создание датасетов
train_dataset = UniversalDataset(X_train, y_train, transform=train_transform)
val_dataset = UniversalDataset(X_val, y_val, transform=val_transform)
test_dataset = UniversalDataset(X_test, y_test, transform=val_transform)

# ============================================================================
# ⚖️ ШАГ 5: ОБРАБОТКА ДИСБАЛАНСА КЛАССОВ
# ============================================================================

print(f"\n{'='*80}")
print(f"            ⚖️ БАЛАНСИРОВКА КЛАССОВ")
print(f"{'='*80}\n")

# Вычисление весов классов
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weights_tensor = torch.FloatTensor(class_weights).to(device)

print(f"📊 Веса классов:")
for idx, weight in enumerate(class_weights):
    print(f"   {CLASSES[idx]:15s}: {weight:.4f}")

# Weighted Random Sampler
class_counts = Counter(y_train)
sample_weights = [1.0 / class_counts[label] for label in y_train]
sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)

# DataLoaders
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=2)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

print(f"\n✅ DataLoaders созданы")

# ============================================================================
# 🧠 ШАГ 6: СОЗДАНИЕ МОДЕЛИ (EfficientNet-B4)
# ============================================================================

print(f"\n{'='*80}")
print(f"            🧠 СОЗДАНИЕ МОДЕЛИ")
print(f"{'='*80}\n")

print(f"🔧 Архитектура: EfficientNet-B4")
print(f"   Классов: {NUM_CLASSES}")
print(f"   Входной размер: {IMG_SIZE}x{IMG_SIZE}")

# Используем EfficientNet-B4 для лучшей точности
model = models.efficientnet_b4(weights='IMAGENET1K_V1')

# Заменяем финальный слой
num_features = model.classifier[1].in_features
model.classifier = nn.Sequential(
    nn.Dropout(p=0.4),
    nn.Linear(num_features, NUM_CLASSES)
)

model = model.to(device)

# Loss и Optimizer
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
optimizer_stage1 = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE_STAGE1)
optimizer_stage2 = optim.Adam(model.parameters(), lr=LEARNING_RATE_STAGE2)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer_stage1, mode='max', factor=0.5, patience=3)

print(f"✅ Модель создана и готова к обучению!\n")

# ============================================================================
# 🏋️ ШАГ 7: ОБУЧЕНИЕ - STAGE 1 (ТОЛЬКО ГОЛОВА)
# ============================================================================

print(f"{'='*80}")
print(f"            🏋️ STAGE 1: ОБУЧЕНИЕ ГОЛОВЫ ({EPOCHS_STAGE1} эпох)")
print(f"{'='*80}\n")

# Замораживаем base model
for param in model.features.parameters():
    param.requires_grad = False

best_val_acc = 0.0
train_losses = []
val_accuracies = []

for epoch in range(EPOCHS_STAGE1):
    # Training
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc=f'Эпоха {epoch+1}/{EPOCHS_STAGE1}')
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)
        
        optimizer_stage1.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer_stage1.step()
        
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        pbar.set_postfix({'loss': f'{running_loss/(pbar.n+1):.4f}', 'acc': f'{100*correct/total:.2f}%'})
    
    train_loss = running_loss / len(train_loader)
    train_acc = 100 * correct / total
    
    # Validation
    model.eval()
    val_correct = 0
    val_total = 0
    
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()
    
    val_acc = 100 * val_correct / val_total
    
    train_losses.append(train_loss)
    val_accuracies.append(val_acc)
    
    print(f"   Эпоха {epoch+1}: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, Val Acc: {val_acc:.2f}%")
    
    # Сохранение лучшей модели
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        os.makedirs('models', exist_ok=True)
        torch.save(model.state_dict(), 'models/universal_model_STAGE1.pth')
        print(f"   ✅ Новая лучшая модель! Val Acc: {val_acc:.2f}%")
    
    scheduler.step(val_acc)

print(f"\n✅ Stage 1 завершен! Лучшая точность: {best_val_acc:.2f}%")

# ============================================================================
# 🏋️ ШАГ 8: ОБУЧЕНИЕ - STAGE 2 (FINE-TUNING)
# ============================================================================

print(f"\n{'='*80}")
print(f"            🏋️ STAGE 2: FINE-TUNING ({EPOCHS_STAGE2} эпох)")
print(f"{'='*80}\n")

# Загружаем лучшую модель из Stage 1
model.load_state_dict(torch.load('models/universal_model_STAGE1.pth'))

# Размораживаем все слои
for param in model.parameters():
    param.requires_grad = True

scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer_stage2, mode='max', factor=0.5, patience=5)

for epoch in range(EPOCHS_STAGE2):
    # Training
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc=f'Эпоха {epoch+1}/{EPOCHS_STAGE2}')
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)
        
        optimizer_stage2.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer_stage2.step()
        
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        pbar.set_postfix({'loss': f'{running_loss/(pbar.n+1):.4f}', 'acc': f'{100*correct/total:.2f}%'})
    
    train_loss = running_loss / len(train_loader)
    train_acc = 100 * correct / total
    
    # Validation
    model.eval()
    val_correct = 0
    val_total = 0
    
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            val_total += labels.size(0)
            val_correct += (predicted == labels).sum().item()
    
    val_acc = 100 * val_correct / val_total
    
    train_losses.append(train_loss)
    val_accuracies.append(val_acc)
    
    print(f"   Эпоха {epoch+1}: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, Val Acc: {val_acc:.2f}%")
    
    # Сохранение лучшей модели
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), 'models/universal_model_BEST.pth')
        print(f"   ✅ Новая лучшая модель! Val Acc: {val_acc:.2f}%")
    
    scheduler.step(val_acc)

print(f"\n✅ Stage 2 завершен! Лучшая точность: {best_val_acc:.2f}%")

# ============================================================================
# 🧪 ШАГ 9: ТЕСТИРОВАНИЕ
# ============================================================================

print(f"\n{'='*80}")
print(f"            🧪 ТЕСТИРОВАНИЕ МОДЕЛИ")
print(f"{'='*80}\n")

# Загружаем лучшую модель
model.load_state_dict(torch.load('models/universal_model_BEST.pth'))
model.eval()

all_preds = []
all_true = []

with torch.no_grad():
    for images, labels in tqdm(test_loader, desc='Тестирование'):
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)
        all_preds.extend(predicted.cpu().numpy())
        all_true.extend(labels.cpu().numpy())

test_acc = accuracy_score(all_true, all_preds)
print(f"\n🎯 Точность на тестовой выборке: {test_acc*100:.2f}%\n")

# Classification Report
print(f"{'='*80}")
print(f"            📋 ДЕТАЛЬНЫЙ ОТЧЕТ")
print(f"{'='*80}\n")
report = classification_report(all_true, all_preds, target_names=CLASSES, zero_division=0)
print(report)

# Confusion Matrix
cm = confusion_matrix(all_true, all_preds)
plt.figure(figsize=(16, 14))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=CLASSES, yticklabels=CLASSES)
plt.title(f'Confusion Matrix - Universal Model\nТочность: {test_acc*100:.2f}%', fontsize=16, fontweight='bold')
plt.ylabel('Истинные классы', fontsize=12, fontweight='bold')
plt.xlabel('Предсказанные классы', fontsize=12, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
os.makedirs('results', exist_ok=True)
plt.savefig('results/confusion_matrix_UNIVERSAL.png', dpi=300, bbox_inches='tight')
print(f"\n✅ Confusion Matrix сохранена: results/confusion_matrix_UNIVERSAL.png")

# Сохранение маппинга классов
import json
class_mapping_file = 'models/universal_class_mapping.json'
with open(class_mapping_file, 'w', encoding='utf-8') as f:
    json.dump({
        'classes': CLASSES,
        'class_to_idx': CLASS_MAPPING,
        'num_classes': NUM_CLASSES,
        'total_images': len(all_images),
        'test_accuracy': float(test_acc)
    }, f, indent=2, ensure_ascii=False)
print(f"✅ Маппинг классов сохранен: {class_mapping_file}")

# Финальное сохранение
torch.save(model.state_dict(), 'models/universal_model_FINAL.pth')
print(f"✅ Финальная модель сохранена: models/universal_model_FINAL.pth")

print(f"\n{'='*80}")
print(f"            🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО!")
print(f"{'='*80}")
print(f"\n🎯 Итоговая точность: {test_acc*100:.2f}%")
print(f"📊 Классов: {NUM_CLASSES}")
print(f"📸 Изображений: {len(all_images)}")
print(f"💾 Модель сохранена: models/universal_model_FINAL.pth\n")

plt.show()


