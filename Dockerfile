FROM python:3.12-alpine

WORKDIR /app

COPY uv.lock pyproject.toml .
RUN pip install uv && uv venv
ENV PATH="/app/.venv/bin:$PATH"

COPY main.py .
COPY assets ./assets
COPY core ./core

EXPOSE 8080
CMD ["uv", "run", "main.py"]



