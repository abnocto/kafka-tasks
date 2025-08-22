FROM python:3.11-slim

WORKDIR /module-1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./main.py .

ENV PYTHONPATH=/module-1
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
