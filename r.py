from db.connection import get_connection

def init_db():
    db = get_connection(True)
    db.execute("UPDATE orders SET tracking_number = NULL WHERE id = %s", (48,))
    db.close()
init_db()