import faust

# Запрещенное слово
class BannedWord(faust.Record, serializer='json'):
    action: str
    word: str

    def __str__(self):
        return f"BannedWord(action='{self.action}', word='{self.word}')"
