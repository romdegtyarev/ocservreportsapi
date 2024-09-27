import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()

DB_HOST = os.getenv('POSTGRES_HOST')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')


def execute_sql_command_and_fetch(query):
    """Executes an SQL query and returns all records."""
    with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

def print_user_ips():
    """Fetches and prints user IPs from the database."""
    print("user_ips:")
    print("-----------------------------")
    results = execute_sql_command_and_fetch("SELECT username, ip_address FROM user_ips;")
    if results:
        for username, ip_address in results:
            print(f"{username:<20} | {ip_address:<15}")
    else:
        print("No user IPs found.")
    print("-----------------------------")

def print_user_sessions():
    """Fetches and prints user sessions from the database."""
    print("user_sessions:")
    print("-----------------------------------")
    results = execute_sql_command_and_fetch("SELECT username, disconnect_time, duration, bytes_in, bytes_out FROM user_sessions;")
    if results:
        for username, disconnect_time, duration, bytes_in, bytes_out in results:
            disconnect_time_str = disconnect_time.strftime('%Y-%m-%d %H:%M:%S') if disconnect_time else "N/A"
            print(f"{username:<20} | {disconnect_time_str:<20} | {duration:<10} | {bytes_in:<10} | {bytes_out:<10}")
    else:
        print("No user sessions found.")
    print("-----------------------------------")

def main():
    print_user_ips()
    print_user_sessions()

if __name__ == "__main__":
    main()

