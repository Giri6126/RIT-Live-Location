# config.py
import os
import mysql.connector
from mysql.connector import Error

# Load .env file if python-dotenv is installed (optional dependency)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — fall back to OS environment or defaults


def get_db_connection():
    """
    Returns a MySQL database connection.
    Credentials are read from environment variables (set in .env or the OS):
        DB_HOST     (default: localhost)
        DB_USER     (default: root)
        DB_PASSWORD (default: Giri2006@)
        DB_NAME     (default: rit_transport)
    """
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", "Giri2006@"),
            database=os.environ.get("DB_NAME", "rit_transport"),
        )
        return conn
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None
