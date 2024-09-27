import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()
print("Loaded environment variables:")
print(os.environ)

DB_HOST = os.getenv('POSTGRES_HOST')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')


def test_db_connection():
    try:
        with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
            print("Database connection successful!")
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                db_version = cursor.fetchone()
                print(f"Database version: {db_version[0]}")
    except Exception as e:
        print(f"Error connecting to the database: {e}")

if __name__ == "__main__":
    test_db_connection()

