import sqlite3

def get_connection():
    return sqlite3.connect("data/miracle_7.db")  # �Ǵ� ':memory:' if in-memory �뵵

def init_db(query):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()
