FROM apache/spark-py:v3.4.0

WORKDIR /analytics

COPY requirements.txt .

USER root

RUN pip install --no-cache-dir -r requirements.txt

USER 185

COPY ./app ./app
COPY ./main.py .

ENV PYTHONPATH=/analytics

CMD ["/opt/spark/bin/spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0", "main.py"]