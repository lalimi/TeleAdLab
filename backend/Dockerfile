FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Переменные окружения
ENV FLASK_APP=run.py
ENV FLASK_ENV=development

# Открываем порт
EXPOSE 5000

# Запуск приложения
CMD ["flask", "run", "--host=0.0.0.0"] 