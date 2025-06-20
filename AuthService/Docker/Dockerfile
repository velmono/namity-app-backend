FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливает рабочую директорию внутри контейнера
WORKDIR /app                               

# Обновляет пакеты
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends build-essential  

# Копирует файл содержащий названия библиотек/зависимостей в контейнер
COPY requirements.txt ./                   

# Обновляет pip и устанавливает зависимости из requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt  

# Копирует все файлы из текущей директории в рабочую директорию контейнера
COPY . .                                   

# Открывает порт 8001 для доступа к микросервису
EXPOSE 8001                                

# Выполняет миграции базы данных и запускает микросервис на Uvicorn
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8001  


