FROM python:3.12-alpine

WORKDIR /app

COPY uv.lock pyproject.toml .
RUN pip install uv && uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

COPY main.py .
COPY assets ./assets
COPY core ./core

EXPOSE 8080
CMD ["python", "main.py"]
