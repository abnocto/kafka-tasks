import random
import uuid

class Item:
    @staticmethod
    def from_dict(dict: dict) -> 'Item':
        return Item(id=dict['id'], name=dict['name'], price=dict['price'])

    @staticmethod
    def generate() -> 'Item':
        id = str(uuid.uuid4())
        name = random.choice(['table', 'chair', 'lamp', 'laptop', 'keyboard', 'mouse', 'monitor', 'printer', 'calendar', 'headphones'])
        price = random.randint(100, 1000)

        return Item(id=id, name=name, price=price)

    def __init__(self, id: str, name: str, price: int):
        self.id = id
        self.name = name
        self.price = price
    
    def __str__(self):
        return f"Item(id='{self.id}', name='{self.name}', price={self.price})"

    def to_dict(self) -> dict:
        return {'id': self.id, 'name': self.name, 'price': self.price}
