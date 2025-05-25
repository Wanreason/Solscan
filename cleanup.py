from tinydb import TinyDB, Query
import time

def cleanup_db(db):
    """Removes old records from TinyDB to prevent excessive storage usage."""
    UserSettings = Query()
    current_time = time.time()
    expiration_time = 30 * 24 * 60 * 60  # 30 days in seconds

    db.remove(UserSettings.timestamp < current_time - expiration_time)
    print("✅ Database cleanup completed.")
