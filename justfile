up:
  docker compose up -d --build

down:
  docker compose down

build:
  docker build -t fastapi-merch-shop-fastapi:latest .

test:
  uv run pytest -v

lint:
  uv run ruff check . --fix

fmt:
  uv run ruff format .

migrate:
  uv run alembic revision --autogenerate -m "$(msg)"

upgrade:
  uv run alembic upgrade head

apply:
  kubectl apply -f k8s/

delete:
  kubectl delete -f k8s/

nodes:
  kubectl get nodes

pods:
  kubectl get pods

restart:
  kubectl rollout restart deployment merch-shop-api
