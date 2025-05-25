from tinydb import TinyDB, Query
import time

db = TinyDB('settings.json')
UserSettings = Query()

def save_setting(user_id, key, value):
    db.upsert({'user_id': user_id, key: value, 'timestamp': time.time()}, UserSettings.user_id == user_id)

def get_setting(user_id, key, default=None):
    result = db.get(UserSettings.user_id == user_id)
    return result[key] if result and key in result else default
