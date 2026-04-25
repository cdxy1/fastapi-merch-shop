up:
  docker compose up -d --build

down:
  docker compose down

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
