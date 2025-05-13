# Предполагается, что ваш Dockerfile основан на образе Python
FROM python:3.11

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование и установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода проекта
COPY . .

# Команда по умолчанию (если нужно, будет переопределена в docker-compose.yml)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]