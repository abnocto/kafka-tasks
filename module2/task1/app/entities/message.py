import faust

# Сообщение
class Message(faust.Record, serializer='json'):
    sender_id: str
    recipient_id: str
    text: str

    def __str__(self):
        return f"Message(sender_id='{self.sender_id}', recipient_id='{self.recipient_id}', text='{self.text}')"
    