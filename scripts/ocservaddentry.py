import os
import psycopg2
import requests
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

TOKEN = os.getenv('TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
DB_HOST = os.getenv('POSTGRES_HOST')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')
VPSFLAG = os.getenv('VPSFLAG')
existing_ip = None


def handle_response(response, message_type):
    """Handles the response from the Telegram API."""
    if response.status_code != 200 or not response.json().get("ok"):
        print(f"Failed to send {message_type}: {response.text}")

def send_message_to_telegram(message):
    """Sends a message to Telegram."""
    if not message:
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": GROUP_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_notification": True
    }
    response = requests.post(url, data=data)
    handle_response(response, "message")

def build_message(username, reason, ip_real, ip_remote, stats_bytes_in, stats_bytes_out, stats_duration):
    """Builds a message for sending to Telegram."""
    global existing_ip

    if reason == "connect" and not existing_ip:
        message = f"{VPSFLAG}: User: {username} connected from IP address: {ip_real}."
        return message
    elif reason != "connect":
        message = f"{VPSFLAG}: Status: {reason} User: {username} IP: {ip_real} TO: {ip_remote} IN: {stats_bytes_in} OUT: {stats_bytes_out} TIME: {stats_duration}"
        return message

    return None

def execute_sql_command(query):
    """Executes an SQL command that does not return data."""
    with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)

def execute_sql_command_and_fetch(query):
    """Executes an SQL query and returns a single record."""
    with psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()

def log_to_database(username, reason, ip_real, ip_remote, stats_bytes_in, stats_bytes_out, stats_duration):
    """Logs the connection or disconnection details to the database."""
    global existing_ip

    if reason == "connect":
        existing_ip = execute_sql_command_and_fetch(f"SELECT ip_address FROM user_ips WHERE username='{username}' AND ip_address='{ip_real}';")
        if not existing_ip:
            execute_sql_command(f"INSERT INTO user_ips (username, ip_address) VALUES ('{username}', '{ip_real}');")
            print(f"Added new IP address: {ip_real} for user: {username}")
    else:
        disconnect_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        execute_sql_command(f"INSERT INTO user_sessions (username, disconnect_time, duration, bytes_in, bytes_out) VALUES ('{username}', '{disconnect_time}', {stats_duration}, {stats_bytes_in}, {stats_bytes_out});")
        print(f"Logged session for user: {username}. Disconnect time: {disconnect_time}, Duration: {stats_duration}, Bytes in: {stats_bytes_in}, Bytes out: {stats_bytes_out}")

    print("Logged session details to database.")

def create_tables():
    """Creates necessary tables in the database if they do not exist."""
    execute_sql_command("""CREATE TABLE IF NOT EXISTS user_ips (username TEXT, ip_address TEXT, PRIMARY KEY (username, ip_address));""")
    execute_sql_command("""CREATE TABLE IF NOT EXISTS user_sessions (username TEXT, disconnect_time TIMESTAMP, duration INTEGER, bytes_in INTEGER, bytes_out INTEGER, PRIMARY KEY (username, disconnect_time));""")

def main():
    """Main function of the application."""
    create_tables()

    username = os.getenv("USERNAME").split('_')[0]
    reason = os.getenv("REASON")
    ip_real = os.getenv("IP_REAL")
    ip_remote = os.getenv("IP_REMOTE")
    stats_bytes_in = os.getenv("STATS_BYTES_IN")
    stats_bytes_out = os.getenv("STATS_BYTES_OUT")
    stats_duration = os.getenv("STATS_DURATION")
    if not stats_duration or not stats_bytes_in or not stats_bytes_out:
        print("One or more statistics values are empty.")
        return

    # Log to database
    log_to_database(username, reason, ip_real, ip_remote, stats_bytes_in, stats_bytes_out, stats_duration)

    # Build message and send message to Telegram
    message = build_message(username, reason, ip_real, ip_remote, stats_bytes_in, stats_bytes_out, stats_duration)
    send_message_to_telegram(message)

if __name__ == "__main__":
    main()
