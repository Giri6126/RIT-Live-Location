# config.py
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """
    Returns a MySQL database connection.
    Raises an exception if connection fails.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",         # replace with your MySQL username
            password="Giri2006@",         # replace with your MySQL password
            database="rit_transport"
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
