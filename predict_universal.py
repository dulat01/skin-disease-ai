"""
🎯 GUI ДЛЯ ТЕСТИРОВАНИЯ УНИВЕРСАЛЬНОЙ МОДЕЛИ
Поддерживает 14+ классов кожных заболеваний
"""

import os
import sys
import json
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ============================================================================
# 📊 КОНФИГУРАЦИЯ
# ============================================================================

MODEL_PATH = 'models/universal_model_FINAL.pth'
MAPPING_PATH = 'models/universal_class_mapping.json'
IMG_SIZE = 224

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ============================================================================
# 🔄 ЗАГРУЗКА МАППИНГА КЛАССОВ
# ============================================================================

if not os.path.exists(MAPPING_PATH):
    print(f"❌ Файл маппинга не найден: {MAPPING_PATH}")
    print(f"   Сначала обучите модель: python train_universal_model.py")
    sys.exit(1)

with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
    mapping_data = json.load(f)

CLASSES = mapping_data['classes']
NUM_CLASSES = mapping_data['num_classes']

print(f"✅ Загружен маппинг: {NUM_CLASSES} классов")

# Описания классов
CLASS_DESCRIPTIONS = {
    # DermaMNIST
    'ACN': ('Акне и Розацеа', '✅', 'Доброкачественное'),
    'ADE': ('Атопический Дерматит', '⚠️', 'Доброкачественное'),
    'BKL': ('Доброкачественный Кератоз', '✅', 'Доброкачественное'),
    'BKL_HAM': ('Доброкачественный Кератоз (HAM)', '✅', 'Доброкачественное'),
    'LPL': ('Красный Плоский Лишай', '⚠️', 'Доброкачественное'),
    'MEL': ('Меланома', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'MEL_PAD': ('Меланома (PAD)', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'MEL_HAM': ('Меланома (HAM)', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'BCC': ('Базальноклеточная Карцинома', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'BCC_PAD': ('Базальноклеточная Карцинома (PAD)', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'BCC_HAM': ('Базальноклеточная Карцинома (HAM)', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'SEK': ('Себорейный Кератоз', '✅', 'Доброкачественное'),
    'SEK_PAD': ('Себорейный Кератоз (PAD)', '✅', 'Доброкачественное'),
    # PAD-UFES-20
    'ACK': ('Актинический Кератоз', '⚠️', 'Предраковое'),
    'NEV': ('Невус (Родинка)', '✅', 'Доброкачественное'),
    'SCC': ('Плоскоклеточная Карцинома', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    # HAM10000
    'AKI': ('Актинический Кератоз (HAM)', '⚠️', 'Предраковое'),
    'DF': ('Дерматофиброма', '✅', 'Доброкачественное'),
    'NV': ('Меланоцитарный Невус', '✅', 'Доброкачественное'),
    'VASC': ('Сосудистые Поражения', '⚠️', 'Доброкачественное'),
}

# ============================================================================
# 🧠 ЗАГРУЗКА МОДЕЛИ
# ============================================================================

print(f"🧠 Загрузка модели: {MODEL_PATH}")

if not os.path.exists(MODEL_PATH):
    print(f"❌ Модель не найдена: {MODEL_PATH}")
    print(f"   Сначала обучите модель: python train_universal_model.py")
    sys.exit(1)

# Создание модели
model = models.efficientnet_b4(weights=None)
num_features = model.classifier[1].in_features
model.classifier = nn.Sequential(
    nn.Dropout(p=0.4),
    nn.Linear(num_features, NUM_CLASSES)
)

# Загрузка весов
state_dict = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(state_dict)
model = model.to(device)
model.eval()

print(f"✅ Модель загружена успешно!\n")

# Трансформации
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ============================================================================
# 🔮 ФУНКЦИЯ ПРЕДСКАЗАНИЯ
# ============================================================================

def predict_image(image_path):
    """Предсказание для изображения"""
    try:
        # Загрузка и предобработка
        img = Image.open(image_path).convert('RGB')
        img_tensor = transform(img).unsqueeze(0).to(device)
        
        # Предсказание
        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            probs = probabilities.cpu().numpy()[0]
        
        # Топ-5 предсказаний
        top5_idx = np.argsort(probs)[::-1][:5]
        top5_probs = probs[top5_idx]
        top5_classes = [CLASSES[idx] for idx in top5_idx]
        
        return img, top5_classes, top5_probs
    
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось обработать изображение:\n{str(e)}")
        return None, None, None

# ============================================================================
# 🖼️ GUI
# ============================================================================

class UniversalModelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"🌟 Универсальная Диагностика Кожных Заболеваний ({NUM_CLASSES} классов)")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Заголовок
        title_frame = tk.Frame(root, bg='#2c3e50', height=80)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame,
            text=f"🌟 УНИВЕРСАЛЬНАЯ СИСТЕМА ДИАГНОСТИКИ\n{NUM_CLASSES} типов кожных заболеваний",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=15)
        
        # Кнопка загрузки
        btn_frame = tk.Frame(root, bg='#f0f0f0')
        btn_frame.pack(pady=10)
        
        self.load_btn = tk.Button(
            btn_frame,
            text="📂 ЗАГРУЗИТЬ ИЗОБРАЖЕНИЕ",
            command=self.load_image,
            font=('Arial', 14, 'bold'),
            bg='#3498db',
            fg='white',
            padx=30,
            pady=15,
            relief=tk.RAISED,
            bd=3
        )
        self.load_btn.pack()
        
        # Основной контейнер
        main_frame = tk.Frame(root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Левая панель (изображение)
        left_frame = tk.Frame(main_frame, bg='white', relief=tk.SOLID, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.image_label = tk.Label(left_frame, text="Загрузите изображение", bg='white', font=('Arial', 12))
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Правая панель (результаты)
        right_frame = tk.Frame(main_frame, bg='white', relief=tk.SOLID, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Результаты
        results_title = tk.Label(
            right_frame,
            text="📊 РЕЗУЛЬТАТЫ АНАЛИЗА",
            font=('Arial', 16, 'bold'),
            bg='white'
        )
        results_title.pack(pady=10)
        
        # График вероятностей
        self.fig, self.ax = plt.subplots(figsize=(7, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Текстовое описание
        self.result_text = tk.Text(right_frame, height=8, font=('Arial', 11), wrap=tk.WORD)
        self.result_text.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Футер
        footer = tk.Label(
            root,
            text="⚠️ ВНИМАНИЕ: Это только помощь в диагностике! Всегда консультируйтесь с врачом-дерматологом!",
            font=('Arial', 10, 'italic'),
            bg='#e74c3c',
            fg='white',
            pady=10
        )
        footer.pack(fill=tk.X)
    
    def load_image(self):
        """Загрузка и анализ изображения"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if not file_path:
            return
        
        # Предсказание
        img, top5_classes, top5_probs = predict_image(file_path)
        
        if img is None:
            return
        
        # Отображение изображения
        img.thumbnail((500, 500))
        from PIL import ImageTk
        photo = ImageTk.PhotoImage(img)
        self.image_label.configure(image=photo, text="")
        self.image_label.image = photo
        
        # Визуализация результатов
        self.display_results(top5_classes, top5_probs)
    
    def display_results(self, classes, probs):
        """Отображение результатов"""
        # График
        self.ax.clear()
        colors = ['#e74c3c' if probs[i] > 0.5 else '#3498db' for i in range(len(classes))]
        bars = self.ax.barh(classes, probs * 100, color=colors)
        self.ax.set_xlabel('Вероятность (%)', fontsize=12, fontweight='bold')
        self.ax.set_title('Топ-5 Предсказаний', fontsize=14, fontweight='bold')
        self.ax.set_xlim(0, 100)
        
        # Добавление процентов на графике
        for i, (bar, prob) in enumerate(zip(bars, probs)):
            self.ax.text(prob * 100 + 2, bar.get_y() + bar.get_height()/2, 
                        f'{prob*100:.1f}%', va='center', fontsize=10, fontweight='bold')
        
        self.canvas.draw()
        
        # Текстовое описание
        self.result_text.delete(1.0, tk.END)
        
        top_class = classes[0]
        top_prob = probs[0]
        
        if top_class in CLASS_DESCRIPTIONS:
            name, emoji, category = CLASS_DESCRIPTIONS[top_class]
            self.result_text.insert(tk.END, f"🎯 ОСНОВНОЙ ДИАГНОЗ:\n", 'bold')
            self.result_text.insert(tk.END, f"{emoji} {name} ({top_class})\n\n", 'result')
            self.result_text.insert(tk.END, f"📊 Уверенность: {top_prob*100:.1f}%\n", 'prob')
            self.result_text.insert(tk.END, f"🏷️ Категория: {category}\n\n", 'category')
        else:
            self.result_text.insert(tk.END, f"🎯 ОСНОВНОЙ ДИАГНОЗ: {top_class}\n", 'bold')
            self.result_text.insert(tk.END, f"📊 Уверенность: {top_prob*100:.1f}%\n\n", 'prob')
        
        # Альтернативные диагнозы
        self.result_text.insert(tk.END, "📋 АЛЬТЕРНАТИВНЫЕ ДИАГНОЗЫ:\n", 'bold')
        for i in range(1, min(5, len(classes))):
            cls = classes[i]
            prob = probs[i]
            if cls in CLASS_DESCRIPTIONS:
                name, emoji, _ = CLASS_DESCRIPTIONS[cls]
                self.result_text.insert(tk.END, f"{i}. {emoji} {name}: {prob*100:.1f}%\n")
            else:
                self.result_text.insert(tk.END, f"{i}. {cls}: {prob*100:.1f}%\n")
        
        # Настройка тегов
        self.result_text.tag_config('bold', font=('Arial', 12, 'bold'))
        self.result_text.tag_config('result', font=('Arial', 13, 'bold'), foreground='#2c3e50')
        self.result_text.tag_config('prob', font=('Arial', 11), foreground='#3498db')
        self.result_text.tag_config('category', font=('Arial', 11, 'bold'), foreground='#e74c3c')

# ============================================================================
# 🚀 ЗАПУСК
# ============================================================================

if __name__ == '__main__':
    root = tk.Tk()
    app = UniversalModelGUI(root)
    root.mainloop()


