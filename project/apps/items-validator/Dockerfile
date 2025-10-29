FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /items-validator

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./main.py .

ENV PYTHONPATH=/items-validator

CMD ["faust", "-A", "main", "worker", "--loglevel=info"]
