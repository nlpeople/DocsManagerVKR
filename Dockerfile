# Используем официальный образ Python
FROM python:3.11

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт для Django
EXPOSE 8000

# Команда по умолчанию (будет переопределена в docker-compose.yml)
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]