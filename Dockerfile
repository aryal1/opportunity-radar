FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8765

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY main.py ./
RUN pip install --no-cache-dir .

EXPOSE 8765
CMD ["python", "main.py"]
