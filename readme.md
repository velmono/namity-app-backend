# Namity Backend

## Описание

Микросервисный backend для музыкального сервиса Namity. Состоит из сервисов:
- **AuthService** — аутентификация и управление пользователями
- **ProfileService** — профили пользователей
- **TrackService** — загрузка и хранение треков
- **PlaylistService** — плейлисты пользователей

Каждый сервис — отдельное FastAPI-приложение, использующее асинхронный PostgreSQL и MinIO для хранения файлов.

---

## Быстрый старт

### 1. Клонируйте репозиторий

```sh
git clone https://github.com/velmono/namity-app-backend.git
cd namity-app-backend
```

### 2. Создайте и настройте переменные окружения

- Скопируйте `.env.example` в `.env` и заполните нужные значения для всех сервисов.
- Для каждого микросервиса есть свой `.env` в соответствующей папке (`AuthService/.env`, `ProfileService/.env` и т.д.).

### 3. Создайте папки для секретных ключей

В каждой папке сервиса создайте папку `secrets`:

```
AuthService/secrets/
ProfileService/secrets/
TrackService/secrets/
PlaylistService/secrets/
```

В эти папки необходимо поместить асимметричные ключи для JWT (private и public).  
Сгенерировать их можно с помощью openssl:

```sh
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```

- Поместите `private.pem` и `public.pem` в папку `secrets` соответствующего сервиса.
- Укажите пути к ключам в `.env` (например, `PRIVATE_KEY_PATH=secrets/private.pem`).

### 4. Запустите сервисы через Docker Compose

```sh
docker compose up --build
```

- Все сервисы, базы данных и MinIO будут подняты автоматически.
- Nginx будет доступен на порту 8080.

---

## Структура проекта

```
namity-app-backend/
│
├── AuthService/
│   ├── app/
│   ├── Docker/
│   ├── secrets/
│   └── ...
├── ProfileService/
│   ├── app/
│   ├── Docker/
│   ├── secrets/
│   └── ...
├── TrackService/
│   ├── app/
│   ├── Docker/
│   ├── secrets/
│   └── ...
├── PlaylistService/
│   ├── app/
│   ├── Docker/
│   ├── secrets/
│   └── ...
├── docker-compose.yml
├── nginx.conf
└── ...
```

---

## Основные зависимости

- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- MinIO (S3-совместимое хранилище)
- Uvicorn
- Alembic (миграции)
- Docker, Docker Compose

---

## Важно

- Не забудьте создать и заполнить папки `secrets` с ключами для каждого сервиса!
- Все переменные окружения должны быть корректно прописаны в `.env` файлах.
- Для работы MinIO используйте данные из `.env` и настройте бакеты при первом запуске.

---
