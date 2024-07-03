import sqlite3
from config import DATABASE

def get_connection():
    conn = sqlite3.connect(DATABASE)
    return conn
