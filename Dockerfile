FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN pip install . uvicorn lxml_html_clean

EXPOSE 8000

CMD ["uvicorn", "jarrl.api:app", "--host", "0.0.0.0", "--port", "8000"]
