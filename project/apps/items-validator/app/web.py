import logging
import os
from faust import web

from app.app import items_validator_app
from app.topics import items_banned_topic
from app.tables import table_items_banned

logger = logging.getLogger(__name__)

def load_template(filename):
    template_path = os.path.join(os.path.dirname(__file__), 'templates', filename)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

@items_validator_app.page('/')
async def index(self, request):
    html = load_template('index.html')
    return self.html(html)

class AddBannedItemView(web.View):
    async def post(self, request):
        data = await request.json()
        item_name = data.get('name')
        
        if not item_name:
            return self.json({'status': 'error'}, status=400)
        
        await items_banned_topic.send(key=item_name, value={'banned': True})
        
        logger.info(f"API: добавление товара '{item_name}' в список запрещенных")
        
        return self.json({'status': 'ok'})

class RemoveBannedItemView(web.View):
    async def post(self, request):
        data = await request.json()
        item_name = data.get('name')
        
        if not item_name:
            return self.json({'status': 'error'}, status=400)
        
        await items_banned_topic.send(key=item_name, value=None)
        
        logger.info(f"API: удаление товара '{item_name}' из списка запрещенных")
        
        return self.json({'status': 'ok'})

class ListBannedItemsView(web.View):
    async def get(self, request):
        banned_items = list(table_items_banned.keys())
        
        return self.json({
            'status': 'ok',
            'items': banned_items
        })

items_validator_app.page('/api/banned/add')(AddBannedItemView)
items_validator_app.page('/api/banned/remove')(RemoveBannedItemView)
items_validator_app.page('/api/banned/list')(ListBannedItemsView)
