import logging
import requests
import json

logger = logging.getLogger(__name__)

class KsqlDBClient:
    def __init__(self):
        self.ksqldb_url = "http://ksqldb-server:8088"
    
    def get_recommendations(self, user_id):
        query = f"SELECT recommendations FROM client_recommendations_table WHERE user_id = '{user_id}';"
        
        try:
            response = requests.post(
                f"{self.ksqldb_url}/query",
                headers={"Content-Type": "application/vnd.ksql.v1+json"},
                json={"ksql": query, "streamsProperties": {}},
                timeout=5
            )
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                if len(lines) > 1 and lines[1].strip():
                    data = json.loads(lines[1])
                    return json.loads(data[0])
                    
        except Exception as e:
            logger.error(f"Ошибка ksqlDB: {e}")
        
        return []
