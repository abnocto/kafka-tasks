import os
import json
import logging

from flask import Flask, request, jsonify, render_template

from app.producer import Producer

app = Flask(__name__)
producer = Producer()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Чтение товаров из items.json
def load_items():
    items_path = os.path.join(os.path.dirname(__file__), 'data', 'items.json')
    with open(items_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/', methods=['GET'])
def index():
    items = load_items()
    return render_template('index.html', items=items)

@app.route('/items/add', methods=['POST'])
def add_items():
    items = request.get_json()

    producer.send_items(items)
    logger.info(f"Товары отправлены в топик items-raw: {', '.join([item.get('name') for item in items])}")

    return jsonify({ "status": "ok" }), 200

def run():
    app.run(host='0.0.0.0', port=8886)
