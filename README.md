# fastapi-merch-shop

REST API магазина мерча с монетной системой. Пользователи получают монеты при регистрации, могут покупать товары и переводить монеты друг другу.

## Стек

| Компонент | Технология |
|-----------|------------|
| Framework | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy 2.0 (asyncpg) |
| Migrations | Alembic |
| Sessions | Redis (refresh tokens) |
| Auth | JWT (access + refresh tokens) |
| Package manager | uv |
| Containerization | Docker / Docker Compose |
| Tests | pytest-asyncio, SQLite in-memory |
| Load testing | Locust |

## Структура проекта

```
src/
├── config.py           # конфигурация из env
├── db.py               # SQLAlchemy engine, сессии
├── main.py             # FastAPI app, lifespan, exception handlers
├── models/
│   ├── user.py         # UserModel
│   ├── item.py         # ItemModel
│   ├── transaction.py  # TransferModel
│   └── purchase.py     # PurchaseModel
├── repository/         # слой БД — только SQL-запросы
│   ├── user.py
│   ├── item.py
│   └── transaction.py
├── service/            # бизнес-логика
│   ├── auth.py
│   └── transaction.py
├── routes/             # HTTP-слой
│   ├── auth.py
│   └── transaction.py
├── schemas/            # Pydantic request/response модели
│   ├── user.py
│   ├── transaction.py
│   └── response.py
└── utils/
    ├── security.py     # JWT, bcrypt, redis-хелперы
    └── redis.py        # RedisClient

migrations/             # Alembic
tests/
├── conftest.py
└── routes/
    ├── test_auth.py
    └── test_transaction.py
```

## API

Все маршруты доступны с префиксом `/api` (задан через `root_path`).

### Auth

| Метод | Путь | Описание | Auth |
|-------|------|----------|------|
| `POST` | `/register` | Регистрация | — |
| `POST` | `/auth` | Логин, возвращает access + refresh токены | — |
| `POST` | `/refresh` | Обновить access token по refresh | Bearer |
| `PATCH` | `/change_password` | Сменить пароль | Bearer |
| `DELETE` | `/logout` | Инвалидировать refresh token | Bearer |

### Транзакции

| Метод | Путь | Описание | Auth |
|-------|------|----------|------|
| `POST` | `/buy/{item}` | Купить товар за монеты | Bearer |
| `POST` | `/sendCoin` | Перевести монеты другому пользователю | Bearer |
| `GET` | `/info` | Баланс, инвентарь, история переводов | Bearer |

**Swagger UI:** `http://localhost:8000/api/docs`

### Примеры запросов

```bash
# Регистрация
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "artem", "password": "secret123"}'

# Логин
curl -X POST http://localhost:8000/api/auth \
  -F "username=artem" -F "password=secret123"

# Купить товар
curl -X POST http://localhost:8000/api/buy/t-shirt \
  -H "Authorization: Bearer <access_token>"

# Перевести монеты
curl -X POST http://localhost:8000/api/sendCoin \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"user": "bob", "amount": 100}'

# Информация о пользователе
curl http://localhost:8000/api/info \
  -H "Authorization: Bearer <access_token>"
```

### Пример ответа `/info`

```json
{
  "coins": 870,
  "inventory": [
    {"type": "t-shirt", "quantity": 1}
  ],
  "CoinHistory": {
    "received": [],
    "sent": [
      {"toUser": "bob", "amount": 50}
    ]
  }
}
```

### Коды ответов

| Код | Описание |
|-----|----------|
| `200` | Успех |
| `201` | Создано (регистрация) |
| `400` | Неверный запрос (недостаток монет, неверный пароль) |
| `401` | Не авторизован |
| `403` | Доступ запрещён |
| `404` | Не найдено |
| `409` | Пользователь уже существует |
| `503` | Redis недоступен |

### Товары

При запуске через `alembic upgrade head` в БД сидируются 11 товаров:

| Товар | Цена |
|-------|------|
| t-shirt | 80 |
| cup | 20 |
| book | 50 |
| pen | 10 |
| powerbank | 200 |
| hoody | 300 |
| umbrella | 200 |
| socks | 10 |
| wallet | 50 |
| pink-hoody | 500 |

Новый пользователь получает **1000 монет** при регистрации.

## Запуск

### Переменные окружения

Скопируйте `.env.example` и заполните:

```bash
cp .env.example .env
```

```env
ALGORITHM=HS256
SECRET_KEY=<сгенерировать: openssl rand -hex 32>
EXPIRATION_SECONDS=3600

REDIS_HOST=localhost
REDIS_PORT=6379

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=changeme
POSTGRES_DB=merch_db
```

### Docker Compose (рекомендуется)

```bash
# Запустить postgres, redis, приложение
just up

# Применить миграции (в первый раз)
just upgrade

# Остановить
just down
```

Или напрямую:

```bash
docker compose up -d --build
docker compose exec fastapi alembic upgrade head
```

### Локально (без Docker)

Нужны запущенные PostgreSQL и Redis.

```bash
# Установить зависимости
uv sync

# Применить миграции
uv run alembic upgrade head

# Запустить
uvicorn src.main:app --reload
```

Приложение: `http://localhost:8000`

## Разработка

```bash
just test      # запустить тесты
just lint      # ruff check --fix
just fmt       # ruff format
just migrate   # создать новую миграцию: just migrate msg="описание"
just upgrade   # применить миграции
```

## Тесты

17 тестов, SQLite in-memory — внешние сервисы не нужны:

```bash
uv run pytest -v
```

Тесты покрывают:

- Регистрацию и логин (успех / дубликат / неверный пароль)
- Refresh и logout токенов
- Смену пароля (успех / неверный старый пароль)
- Покупку товара (успех / недостаток монет / товар не найден)
- Перевод монет (успех / недостаток / получатель не найден)
- Получение информации о пользователе

## Деплой в Minikube

PostgreSQL и Redis запускаются локально (через `docker compose` или нативно). Приложение деплоится в minikube и обращается к ним через `host.docker.internal`.

### Требования

```bash
brew install minikube kubectl
minikube start --driver=docker
```

### Структура манифестов

```
k8s/
├── configmap.yaml   # ALGORITHM, REDIS_HOST, POSTGRES_HOST и т.д.
├── secrets.yaml     # SECRET_KEY, POSTGRES_PASSWORD
├── deployment.yaml  # Deployment (5 реплик), NodePort сервис
└── service.yaml     # NodePort :30007
```

### Сборка образа

Образ собирается внутри Docker-контекста minikube через `docker compose build` — имя образа берётся из `docker-compose.yml`:

```bash
eval $(minikube docker-env)
docker compose build
```

### Деплой

```bash
kubectl apply -f k8s/
```

Применить миграции:

```bash
kubectl exec deploy/merch-shop-api -- alembic upgrade head
```

Узнать адрес сервиса:

```bash
minikube service merch-shop-api-service --url
# → http://<minikube-ip>:30007
```

### Обновление после изменений в коде

```bash
eval $(minikube docker-env)
docker compose build
kubectl rollout restart deployment/merch-shop-api
```

### Полезные команды

```bash
# логи
kubectl logs -l app=merch-shop-api -f

# статус подов
kubectl get pods

# зайти в под
kubectl exec -it deploy/merch-shop-api -- /bin/bash

# применить миграции
kubectl exec deploy/merch-shop-api -- alembic upgrade head
```

## Лицензия

MIT — см. [LICENSE](LICENSE).
