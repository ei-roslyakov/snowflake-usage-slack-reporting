FROM --platform=amd64 python:3.10.13-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app.py ./
COPY .env.example ./.env

RUN chown -R appuser:appuser /app
USER appuser

CMD ["python", "app.py"]
