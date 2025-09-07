import faust

# Забаненный пользователь
class BannedUser(faust.Record, serializer='json'):
    action: str
    user_id: str
    banned_user_id: str

    def __str__(self):
        return f"BannedUser(action='{self.action}', user_id='{self.user_id}', banned_user_id='{self.banned_user_id}')"
