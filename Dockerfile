FROM python:3.12-slim

WORKDIR /app

# Зависимости отдельным слоем — кешируются при rebuild
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код проекта
COPY . .

# Папка для SQLite БД
RUN mkdir -p /app/instance

EXPOSE 5000

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "app.py"]
