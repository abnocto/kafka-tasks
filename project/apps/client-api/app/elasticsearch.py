import logging
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    def __init__(self):
        self.client = Elasticsearch(
            hosts=["http://elasticsearch:9200"],
            request_timeout=30
        )
    
    def search_items(self, query_text, size=3):
        try:
            response = self.client.search(
                index="items-validated",
                size=size,
                query={
                    "multi_match": {
                        "query": query_text,
                        "fields": ["name^3", "description^2", "category", "brand", "tags"],
                        "fuzziness": "AUTO"
                    }
                }
            )

            hits = response.get('hits', {}).get('hits', [])
            return [hit['_source'] for hit in hits]
        
        except Exception as e:
            logger.error(f'Ошибка поиска в Elasticsearch: {e}')
            return []

