"""
🎯 GUI ДЛЯ ТЕСТИРОВАНИЯ УНИВЕРСАЛЬНОЙ МОДЕЛИ
Поддерживает 14+ классов кожных заболеваний через backend API
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from backend_client import BackendClient

# Описания классов
CLASS_DESCRIPTIONS = {
    'ACN': ('Акне и Розацеа', '✅', 'Доброкачественное'),
    'ADE': ('Атопический Дерматит', '⚠️', 'Доброкачественное'),
    'BKL': ('Доброкачественный Кератоз', '✅', 'Доброкачественное'),
    'LPL': ('Красный Плоский Лишай', '⚠️', 'Доброкачественное'),
    'MEL': ('Меланома', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'BCC': ('Базальноклеточная Карцинома', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'SEK': ('Себорейный Кератоз', '✅', 'Доброкачественное'),
    'ACK': ('Актинический Кератоз', '⚠️', 'Предраковое'),
    'NEV': ('Невус (Родинка)', '✅', 'Доброкачественное'),
    'SCC': ('Плоскоклеточная Карцинома', '☠️', 'ЗЛОКАЧЕСТВЕННОЕ'),
    'DF': ('Дерматофиброма', '✅', 'Доброкачественное'),
    'NV': ('Меланоцитарный Невус', '✅', 'Доброкачественное'),
    'VASC': ('Сосудистые Поражения', '⚠️', 'Доброкачественное'),
}

class UniversalSkinDiseaseApp:
    def __init__(self, root):
        self.root = root
        self.current_image_path = None

        try:
            self.client = BackendClient()
            if not self.client.health_check():
                raise ConnectionError("Backend not responding")
            self.backend_connected = True
        except Exception as e:
            self.backend_connected = False
            self.error_msg = str(e)

        self.root.title("🎯 УНИВЕРСАЛЬНАЯ ДИАГНОСТИКА ЗАБОЛЕВАНИЙ КОЖИ")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2C3E50')

        # Заголовок
        header = tk.Frame(root, bg='#34495E')
        header.pack(fill=tk.X, padx=10, pady=10)

        title = tk.Label(
            header,
            text="🎯 УНИВЕРСАЛЬНАЯ ДИАГНОСТИКА ЗАБОЛЕВАНИЙ КОЖИ",
            font=("Arial", 20, "bold"),
            bg='#34495E',
            fg='white'
        )
        title.pack(pady=15)

        # Информация
        info_frame = tk.Frame(root, bg='#2C3E50')
        info_frame.pack(fill=tk.X, padx=20, pady=5)

        status_text = "✅ Backend Connected" if self.backend_connected else "❌ Backend Disconnected"
        status_color = '#2ECC71' if self.backend_connected else '#E74C3C'

        model_info = tk.Label(
            info_frame,
            text=f"{status_text} | 14+ классов заболеваний",
            font=("Arial", 10),
            bg='#2C3E50',
            fg=status_color
        )
        model_info.pack()

        if not self.backend_connected:
            error_label = tk.Label(
                info_frame,
                text=f"Error: {self.error_msg}",
                font=("Arial", 9),
                bg='#2C3E50',
                fg='#E74C3C'
            )
            error_label.pack()

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
            padx=30,
            pady=15,
            state=tk.NORMAL if self.backend_connected else tk.DISABLED
        )
        self.load_btn.pack()

        # Основной контент
        content = tk.Frame(root, bg='#2C3E50')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Левая колонна - изображение
        left_frame = tk.Frame(content, bg='#34495E')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        img_label = tk.Label(left_frame, text="ИЗОБРАЖЕНИЕ", bg='#34495E', fg='white', font=("Arial", 12, "bold"))
        img_label.pack(pady=10)

        self.image_display = tk.Label(left_frame, bg='#1C2833', width=30, height=20)
        self.image_display.pack(pady=10, fill=tk.BOTH, expand=True)

        # Правая колонна - результаты
        right_frame = tk.Frame(content, bg='#34495E')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

        result_label = tk.Label(right_frame, text="РЕЗУЛЬТАТЫ", bg='#34495E', fg='white', font=("Arial", 12, "bold"))
        result_label.pack(pady=10)

        # Основное предсказание
        self.main_prediction = tk.Frame(right_frame, bg='#2C3E50')
        self.main_prediction.pack(fill=tk.BOTH, expand=True, pady=10)

        self.pred_text = tk.Label(self.main_prediction, text="", bg='#2C3E50', fg='#ECF0F1', font=("Arial", 11), wraplength=350, justify=tk.LEFT)
        self.pred_text.pack(fill=tk.BOTH, expand=True)

        # График вероятностей
        self.canvas_frame = tk.Frame(right_frame, bg='#2C3E50')
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)

    def load_image(self):
        """Загрузить изображение"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )

        if file_path:
            self.current_image_path = file_path

            # Отображение изображения
            image = Image.open(file_path)
            image.thumbnail((250, 300))
            photo = ImageTk.PhotoImage(image)
            self.image_display.config(image=photo)
            self.image_display.image = photo

            # Предсказание
            self.predict()

    def predict(self):
        """Получить предсказание от backend"""
        if not self.current_image_path or not self.backend_connected:
            messagebox.showerror("Ошибка", "Загрузите изображение и проверьте соединение")
            return

        try:
            self.load_btn.config(state=tk.DISABLED, text="⏳ АНАЛИЗИРОВАНИЕ...")
            self.root.update()

            # Запрос к серверу
            result = self.client.predict(self.current_image_path)

            if 'data' in result:
                data = result['data']
            else:
                data = result

            # Основное предсказание
            predicted_class = data.get('predicted_class', 'Unknown')
            confidence = data.get('confidence', 0) * 100

            # Получить описание класса
            desc_info = CLASS_DESCRIPTIONS.get(predicted_class, (predicted_class, '❓', 'Неизвестно'))
            class_name, emoji, severity = desc_info

            color = '#E74C3C' if data.get('is_malignant') else '#2ECC71'

            pred_text = f"{emoji} {class_name}\nВероятность: {confidence:.1f}%\nТяжесть: {severity}"
            self.pred_text.config(text=pred_text, fg=color)

            # График вероятностей
            self.draw_probabilities(data.get('top_predictions', []))

        except ConnectionError as e:
            messagebox.showerror("Ошибка подключения", f"Backend недоступен:\n{e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе:\n{e}")
        finally:
            self.load_btn.config(state=tk.NORMAL, text="📂 ЗАГРУЗИТЬ ИЗОБРАЖЕНИЕ")

    def draw_probabilities(self, predictions):
        """Нарисовать график вероятностей"""
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        if not predictions:
            return

        # Данные для графика
        classes = []
        probs = []

        for pred in predictions[:10]:
            class_name = pred.get('class_name', 'Unknown')
            class_key = ''.join(c for c in class_name if c.isalpha()).upper()[:3]
            classes.append(class_key)
            probs.append(pred.get('confidence', 0) * 100)

        # Создание графика
        fig, ax = plt.subplots(figsize=(6, 4), dpi=80)
        colors = ['#E74C3C' if p > 50 else '#F39C12' if p > 30 else '#2ECC71' for p in probs]
        bars = ax.barh(classes, probs, color=colors)

        ax.set_xlabel('Вероятность (%)', color='white')
        ax.set_xlim(0, 100)
        ax.set_facecolor('#2C3E50')
        ax.tick_params(colors='white')

        fig.patch.set_facecolor('#2C3E50')

        # Встроить график в tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalSkinDiseaseApp(root)
    root.mainloop()
