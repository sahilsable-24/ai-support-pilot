FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

RUN uv pip install torch --index-url https://download.pytorch.org/whl/cpu --reinstall-package torch

COPY . .

EXPOSE 7860

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]