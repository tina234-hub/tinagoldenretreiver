import os
import sqlite3
import mysql.connector


# Load environment variables from .env file


class Database:
    def __init__(self, use_mysql=False):
        self.use_mysql = False

        if use_mysql:
            self.conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", ""),
                port=int(os.getenv("DB_PORT", 3306))
            )
        else:
            db_path = os.path.join(os.path.dirname(__file__), "database.db")
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row

        self.cursor = self.conn.cursor()

    def execute(self, query, params=None):
        try:
            if not self.use_mysql:
                query = query.replace("%s", "?")
            self.cursor.execute(query, params or ())
            self.conn.commit()
        except Exception as e:
            print("Database Error:", e)
            raise

    def fetchall(self):
        return [dict(row) for row in self.cursor.fetchall()]

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        self.cursor.close()
        self.conn.close()

def get_connection(f=True):
    
    return Database(False)
