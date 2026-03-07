# config.py
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """
    Returns a MySQL database connection.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Giri2006@",
            database="rit_transport"
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
