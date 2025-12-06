"""
🔬 Диагностика заболеваний кожи - Графический интерфейс
Простой GUI для тестирования обученной модели на одном изображении
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import torch
import torch.nn as nn
from torchvision import models, transforms
import json

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
MODEL_PATH = 'models/final_model_CAS.pth'
CLASS_MAPPING_PATH = 'models/class_mapping_ru.json'
IMG_SIZE = 224

# Словарь опасности заболеваний
MALIGNANCY = {
    "Меланома": "ЗЛОКАЧЕСТВЕННАЯ",
    "Базальноклеточная карцинома": "ЗЛОКАЧЕСТВЕННАЯ", 
    "Плоскоклеточная карцинома": "ЗЛОКАЧЕСТВЕННАЯ",
    "Актинический кератоз": "ЗЛОКАЧЕСТВЕННАЯ",
    "Невус (родинка)": "ДОБРОКАЧЕСТВЕННАЯ",
    "Себорейный кератоз": "ДОБРОКАЧЕСТВЕННАЯ"
}

# ============================================================================
# ЗАГРУЗКА МОДЕЛИ
# ============================================================================
def load_model():
    """Загрузка обученной модели"""
    print("🔄 Загрузка модели...")
    
    # Загружаем маппинг классов
    if os.path.exists(CLASS_MAPPING_PATH):
        with open(CLASS_MAPPING_PATH, 'r', encoding='utf-8') as f:
            class_names_dict = json.load(f)
            class_names = [class_names_dict[str(i)] for i in range(len(class_names_dict))]
    else:
        class_names = [
            "Актинический кератоз",
            "Базальноклеточная карцинома", 
            "Меланома",
            "Невус (родинка)",
            "Плоскоклеточная карцинома",
            "Себорейный кератоз"
        ]
    
    # Создаём модель
    model = models.resnet18(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(class_names))
    
    # Загружаем веса
    if not os.path.exists(MODEL_PATH):
        print(f"❌ ОШИБКА: Модель не найдена: {MODEL_PATH}")
        return None, None
    
    state_dict = torch.load(MODEL_PATH, map_location='cpu')
    model.load_state_dict(state_dict)
    model.eval()
    
    print("✅ Модель загружена!")
    return model, class_names

# ============================================================================
# ПРЕДСКАЗАНИЕ
# ============================================================================
def predict_image(model, image_path, class_names):
    """Предсказание для одного изображения"""
    
    # Трансформации
    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Загрузка изображения
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0)
    
    # Предсказание
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        
    return probabilities.numpy()

# ============================================================================
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ============================================================================
class SkinDiseaseApp:
    def __init__(self, root, model, class_names):
        self.root = root
        self.model = model
        self.class_names = class_names
        self.current_image_path = None
        
        # Настройка окна
        self.root.title("🔬 ДИАГНОСТИКА ЗАБОЛЕВАНИЙ КОЖИ")
        self.root.geometry("900x700")
        self.root.configure(bg='#2C3E50')
        
        # Заголовок
        header = tk.Frame(root, bg='#34495E', height=80)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        title = tk.Label(
            header,
            text="🔬 ДИАГНОСТИКА ЗАБОЛЕВАНИЙ КОЖИ",
            font=("Arial", 20, "bold"),
            bg='#34495E',
            fg='white'
        )
        title.pack(pady=15)
        
        # Информация о модели
        info_frame = tk.Frame(root, bg='#2C3E50')
        info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        model_info = tk.Label(
            info_frame,
            text="ResNet18 | Точность: 77.10% | CAS_ISIC Adapted",
            font=("Arial", 10),
            bg='#2C3E50',
            fg='#BDC3C7'
        )
        model_info.pack()
        
        # Кнопка загрузки
        btn_frame = tk.Frame(root, bg='#2C3E50')
        btn_frame.pack(pady=15)
        
        self.load_btn = tk.Button(
            btn_frame,
            text="📂 ЗАГРУЗИТЬ ИЗОБРАЖЕНИЕ",
            command=self.load_image,
            font=("Arial", 14, "bold"),
            bg='#3498DB',
            fg='white',
            activebackground='#2980B9',
            activeforeground='white',
            padx=30,
            pady=15,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.load_btn.pack()
        
        # Контейнер для изображения и результатов
        content_frame = tk.Frame(root, bg='#2C3E50')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Левая панель - изображение
        left_panel = tk.Frame(content_frame, bg='#34495E', relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        img_label = tk.Label(
            left_panel,
            text="Анализируемое изображение",
            font=("Arial", 12, "bold"),
            bg='#34495E',
            fg='white'
        )
        img_label.pack(pady=10)
        
        self.image_label = tk.Label(left_panel, bg='#ECF0F1')
        self.image_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Правая панель - результаты
        right_panel = tk.Frame(content_frame, bg='#34495E', relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # Основной диагноз
        diag_header = tk.Label(
            right_panel,
            text="🎯 ОСНОВНОЙ ДИАГНОЗ",
            font=("Arial", 14, "bold"),
            bg='#34495E',
            fg='white'
        )
        diag_header.pack(pady=15)
        
        self.diagnosis_label = tk.Label(
            right_panel,
            text="Базальноклеточная карцинома",
            font=("Arial", 16, "bold"),
            bg='#34495E',
            fg='white',
            wraplength=300
        )
        self.diagnosis_label.pack(pady=5)
        
        self.malignancy_label = tk.Label(
            right_panel,
            text="🔴 ЗЛОКАЧЕСТВЕННАЯ",
            font=("Arial", 12, "bold"),
            bg='#34495E',
            fg='#E74C3C'
        )
        self.malignancy_label.pack(pady=5)
        
        self.confidence_label = tk.Label(
            right_panel,
            text="Уверенность: 62.09%",
            font=("Arial", 14, "bold"),
            bg='#34495E',
            fg='#3498DB'
        )
        self.confidence_label.pack(pady=10)
        
        self.description_label = tk.Label(
            right_panel,
            text="Самая распространенная форма рака кожи",
            font=("Arial", 10),
            bg='#34495E',
            fg='#BDC3C7',
            wraplength=300
        )
        self.description_label.pack(pady=5)
        
        # ТОП-3 вероятности
        top3_header = tk.Label(
            right_panel,
            text="📊 ТОП-3 ВЕРОЯТНОСТИ",
            font=("Arial", 12, "bold"),
            bg='#34495E',
            fg='white'
        )
        top3_header.pack(pady=(20, 10))
        
        self.top3_frame = tk.Frame(right_panel, bg='#34495E')
        self.top3_frame.pack(fill=tk.BOTH, expand=True, padx=15)
        
        # Предупреждение
        warning_frame = tk.Frame(root, bg='#E74C3C', height=60)
        warning_frame.pack(fill=tk.X, padx=20, pady=10)
        
        warning = tk.Label(
            warning_frame,
            text="⚠️ ВНИМАНИЕ: Это только помощь в диагностике!\nВсегда консультируйтесь с врачом-дерматологом!",
            font=("Arial", 9, "bold"),
            bg='#E74C3C',
            fg='white'
        )
        warning.pack(pady=10)
        
    def load_image(self):
        """Загрузка и анализ изображения"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg"), ("Все файлы", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.current_image_path = file_path
            
            # Показываем изображение
            img = Image.open(file_path)
            img.thumbnail((350, 350), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
            # Получаем предсказание
            probabilities = predict_image(self.model, file_path, self.class_names)
            
            # Обновляем результаты
            self.update_results(probabilities)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{str(e)}")
    
    def update_results(self, probabilities):
        """Обновление результатов на экране"""
        # ТОП-1 (основной диагноз)
        top_idx = probabilities.argmax()
        top_class = self.class_names[top_idx]
        top_prob = probabilities[top_idx] * 100
        
        self.diagnosis_label.config(text=top_class)
        self.confidence_label.config(text=f"Уверенность: {top_prob:.2f}%")
        
        # Определяем опасность
        malignancy = MALIGNANCY.get(top_class, "НЕИЗВЕСТНО")
        if "ЗЛОКАЧЕСТВЕННАЯ" in malignancy:
            self.malignancy_label.config(text="🔴 ЗЛОКАЧЕСТВЕННАЯ", fg='#E74C3C')
            self.description_label.config(text="Требуется срочная консультация онколога!")
        else:
            self.malignancy_label.config(text="🟢 ДОБРОКАЧЕСТВЕННАЯ", fg='#27AE60')
            self.description_label.config(text="Рекомендуется консультация дерматолога")
        
        # ТОП-3
        top3_indices = probabilities.argsort()[-3:][::-1]
        
        # Очищаем предыдущие результаты
        for widget in self.top3_frame.winfo_children():
            widget.destroy()
        
        # Цвета для прогресс-баров
        colors = ['#27AE60', '#3498DB', '#95A5A6']
        
        for i, idx in enumerate(top3_indices):
            class_name = self.class_names[idx]
            prob = probabilities[idx] * 100
            
            # Контейнер для элемента
            item_frame = tk.Frame(self.top3_frame, bg='#34495E')
            item_frame.pack(fill=tk.X, pady=5)
            
            # Текст
            text = f"{i+1}. {class_name}: {prob:.2f}%"
            label = tk.Label(
                item_frame,
                text=text,
                font=("Arial", 9),
                bg='#34495E',
                fg='white',
                anchor='w'
            )
            label.pack(fill=tk.X, padx=5)
            
            # Прогресс-бар
            bar_bg = tk.Frame(item_frame, bg='#2C3E50', height=8)
            bar_bg.pack(fill=tk.X, padx=5, pady=2)
            
            bar_width = int(prob * 2.5)  # Масштаб для визуализации
            bar = tk.Frame(bar_bg, bg=colors[i], height=8, width=bar_width)
            bar.pack(side=tk.LEFT)

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================
def main():
    print("\n" + "="*80)
    print("🔬 ДИАГНОСТИКА ЗАБОЛЕВАНИЙ КОЖИ".center(80))
    print("="*80 + "\n")
    
    # Загрузка модели
    model, class_names = load_model()
    
    if model is None:
        messagebox.showerror(
            "Ошибка",
            f"Не удалось загрузить модель!\nПроверьте наличие файла: {MODEL_PATH}"
        )
        return
    
    # Запуск GUI
    root = tk.Tk()
    app = SkinDiseaseApp(root, model, class_names)
    root.mainloop()

if __name__ == "__main__":
    main()

