"""
🔬 Диагностика заболеваний кожи - Графический интерфейс
GUI для тестирования модели через backend API
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
from pathlib import Path
from backend_client import BackendClient

# Словарь опасности заболеваний
MALIGNANCY = {
    "Меланома": "ЗЛОКАЧЕСТВЕННАЯ",
    "Базальноклеточная карцинома": "ЗЛОКАЧЕСТВЕННАЯ",
    "Плоскоклеточная карцинома": "ЗЛОКАЧЕСТВЕННАЯ",
    "Актинический кератоз": "ЗЛОКАЧЕСТВЕННАЯ",
    "Невус (родинка)": "ДОБРОКАЧЕСТВЕННАЯ",
    "Себорейный кератоз": "ДОБРОКАЧЕСТВЕННАЯ"
}

class SkinDiseaseApp:
    def __init__(self, root):
        self.root = root
        self.current_image_path = None

        # Инициализация клиента
        try:
            self.client = BackendClient()
            if not self.client.health_check():
                raise ConnectionError("Backend not responding")
            self.backend_connected = True
        except Exception as e:
            self.backend_connected = False
            self.error_msg = str(e)

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

        status_text = "✅ Backend Connected" if self.backend_connected else "❌ Backend Disconnected"
        status_color = '#2ECC71' if self.backend_connected else '#E74C3C'

        model_info = tk.Label(
            info_frame,
            text=f"{status_text} | ResNet18 | 77.10% | CAS_ISIC",
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
            activeforeground='white',
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

        self.image_display = tk.Label(left_frame, bg='#1C2833', width=30, height=15)
        self.image_display.pack(pady=10)

        # Правая колонна - результаты
        right_frame = tk.Frame(content, bg='#34495E')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

        result_label = tk.Label(right_frame, text="РЕЗУЛЬТАТЫ ДИАГНОСТИКИ", bg='#34495E', fg='white', font=("Arial", 12, "bold"))
        result_label.pack(pady=10)

        # Прогноз
        self.prediction_frame = tk.Frame(right_frame, bg='#2C3E50')
        self.prediction_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.prediction_label = tk.Label(self.prediction_frame, text="", bg='#2C3E50', fg='#ECF0F1', font=("Arial", 12), wraplength=300, justify=tk.LEFT)
        self.prediction_label.pack(fill=tk.BOTH, expand=True)

        # Топ-3 предсказания
        top_label = tk.Label(right_frame, text="ТОП-3 ПРЕДСКАЗАНИЯ", bg='#34495E', fg='white', font=("Arial", 11, "bold"))
        top_label.pack(pady=10)

        self.top_frame = tk.Frame(right_frame, bg='#2C3E50')
        self.top_frame.pack(fill=tk.BOTH, expand=True)

        self.top_label = tk.Label(self.top_frame, text="", bg='#2C3E50', fg='#ECF0F1', font=("Arial", 9), wraplength=300, justify=tk.LEFT)
        self.top_label.pack(fill=tk.BOTH, expand=True)

    def load_image(self):
        """Загрузить изображение"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )

        if file_path:
            self.current_image_path = file_path

            # Отображение изображения
            image = Image.open(file_path)
            image.thumbnail((250, 250))
            photo = ImageTk.PhotoImage(image)
            self.image_display.config(image=photo)
            self.image_display.image = photo

            # Предсказание
            self.predict()

    def predict(self):
        """Получить предсказание от backend"""
        if not self.current_image_path or not self.backend_connected:
            messagebox.showerror("Ошибка", "Загрузите изображение и проверьте соединение с backend")
            return

        try:
            self.load_btn.config(state=tk.DISABLED, text="⏳ АНАЛИЗИРОВАНИЕ...")
            self.root.update()

            # Отправка на сервер
            result = self.client.predict(self.current_image_path)

            # Проверка успеха
            if 'data' in result:
                data = result['data']
            else:
                data = result

            # Основное предсказание
            predicted_class = data.get('predicted_class', 'Unknown')
            confidence = data.get('confidence', 0) * 100
            is_malignant = data.get('is_malignant', False)

            malignancy_status = MALIGNANCY.get(predicted_class, "НЕИЗВЕСТНО")
            color = '#E74C3C' if is_malignant else '#2ECC71'

            prediction_text = f"Диагноз: {predicted_class}\nВероятность: {confidence:.1f}%\nСтатус: {malignancy_status}"
            self.prediction_label.config(text=prediction_text, fg=color)

            # Топ-3
            top_predictions = data.get('top_predictions', [])
            top_text = ""
            for i, pred in enumerate(top_predictions[:3], 1):
                status = "🔴 ОПАСНО" if pred.get('is_malignant') else "🟢 БЕЗОПАСНО"
                top_text += f"{i}. {pred.get('class_name', 'Unknown')}\n   Вероятность: {pred.get('confidence', 0)*100:.1f}% {status}\n\n"

            self.top_label.config(text=top_text)

        except ConnectionError as e:
            messagebox.showerror("Ошибка подключения", f"Backend недоступен:\n{e}")
        except Exception as e:
            messagebox.showerror("Ошибка предсказания", f"Ошибка при анализе:\n{e}")
        finally:
            self.load_btn.config(state=tk.NORMAL, text="📂 ЗАГРУЗИТЬ ИЗОБРАЖЕНИЕ")

if __name__ == "__main__":
    root = tk.Tk()
    app = SkinDiseaseApp(root)
    root.mainloop()
