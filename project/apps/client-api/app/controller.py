import logging
import json

from flask import Flask, request, jsonify, render_template

from app.producer import Producer
from app.elasticsearch import ElasticsearchClient
from app.ksqldb import KsqlDBClient

app = Flask(__name__)
producer = Producer()
elasticsearch_client = ElasticsearchClient()
ksqldb_client = KsqlDBClient()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/items/search', methods=['POST'])
def search_items():
    client_search_request = request.get_json()

    user_id = client_search_request.get('user_id')
    query = client_search_request.get('search')
    
    # Ищем товары в Elasticsearch
    items = elasticsearch_client.search_items(query)
    logger.info(f"Товары найдены в Elasticsearch: {', '.join([item.get('name') for item in items])}")

    # Отправляем пользовательский запрос в топик client-search-requests для аналитики
    producer.send_client_search_request({"user_id": user_id, "query": query, "result": json.dumps(items)})
    logger.info(f"Пользовательский запрос отправлен в топик client-search-requests: {user_id}, query='{query}', найдено товаров: {len(items)}")
    
    return jsonify(items), 200

@app.route('/items/recommend', methods=['POST'])
def recommend_items():
    user_id = request.get_json().get('user_id')

    recommendations = ksqldb_client.get_recommendations(user_id)
    logger.info(f"Рекомендации получены из ksqlDB: {', '.join([item.get('name') for item in recommendations])}")
    
    return jsonify(recommendations), 200

def run():
    app.run(host='0.0.0.0', port=8887)
