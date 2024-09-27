#!/usr/bin/env python3
import os
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from datetime import datetime, timedelta
import schedule
import time
import requests
import logging
import psycopg2
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv('TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
SCHEDULED_TASK_DELAY = int(os.getenv('SCHEDULED_TASK_DELAY'))
DIRECTORY = os.getenv('DIRECTORY')
DB_HOST = os.getenv('POSTGRES_HOST')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')
TEST_MODE = os.getenv("TEST_MODE", "false")
VPSFLAG = os.getenv('VPSFLAG')

matplotlib_logger = logging.getLogger('matplotlib')
matplotlib_logger.setLevel(logging.WARNING)
logger = logging.getLogger('my_report_logging')
data_storage = {}
data_storage_month = {}


def handle_response(response, message_type):
    """Handles the response from the Telegram API."""
    if response.status_code != 200 or not response.json().get("ok"):
        logger.error(f"Failed to send {message_type}: {response.text}")

def send_photo_to_telegram(photo_path, caption):
    """Sends a photo to the Telegram chat."""
    if TEST_MODE.lower() == "true":
        print(f"Test Mode: Would send photo: {photo_path} with caption: {caption}")
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                    'chat_id': GROUP_CHAT_ID,
                    'caption': caption
            }
            response = requests.post(url, data=data, files=files)
            handle_response(response, "photo")

def create_and_send_chart(users, outgoing_bytes, incoming_bytes, connections, durations):
    """Creates and sends a chart of data usage."""
    plt.title('Кто сколько съел')

    num_users = len(users)
    colors = cm.get_cmap('rainbow', num_users)
    step = num_users // max(len(users), 1)  # Step for selecting colors
    selected_colors = [colors(i * step) for i in range(max(len(users), 1))]

    # Create the first pie chart for outgoing traffic
    plt.figure(figsize=(15, 12))

    plt.subplot(2, 2, 1)  # First chart
    wedges, texts, autotexts = plt.pie(outgoing_bytes, autopct='%1.1f%%', startangle=90, colors=selected_colors, textprops=dict(color="black"))
    plt.title('User Share in Outgoing Traffic')
    plt.axis('equal')  # To make the pie chart circular
    plt.legend(wedges, users, title="Users", loc="lower center", ncol=1)

    # Create the second pie chart for incoming traffic
    plt.subplot(2, 2, 2)  # Second chart
    wedges, texts, autotexts = plt.pie(incoming_bytes, autopct='%1.1f%%', startangle=90, colors=selected_colors, textprops=dict(color="black"))
    plt.title('User Share in Incoming Traffic')
    plt.axis('equal')  # To make the pie chart circular
    plt.legend(wedges, users, title="Users", loc="lower center", ncol=1)

    # Create the third chart for connections
    plt.subplot(2, 2, 3)  # Third chart
    plt.bar(users, connections, color=selected_colors)
    plt.title('Number of Connections')
    plt.xlabel('Users')
    plt.ylabel('Connections')

    # Create the fourth chart for durations
    plt.subplot(2, 2, 4)  # Fourth chart
    plt.bar(users, durations, color=selected_colors)
    plt.title('Total Duration (seconds)')
    plt.xlabel('Users')
    plt.ylabel('Duration (s)')

    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)

    output_file = os.path.join(DIRECTORY, 'usage_report.png')
    plt.savefig(output_file)
    plt.close()

    # Get date
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Calculate total outgoing and incoming bytes
    total_outgoing = sum(outgoing_bytes)
    total_incoming = sum(incoming_bytes)
    total_connections = sum(connections)
    total_duration = sum(durations)
    # Convert bytes to gigabytes
    total_outgoing_gb = total_outgoing / (1024 ** 3)
    total_incoming_gb = total_incoming / (1024 ** 3)
    # Log the total bytes in gigabytes
    logger.info(f"Total Outgoing Bytes: {total_outgoing} bytes ({total_outgoing_gb:.2f} GB)")
    logger.info(f"Total Incoming Bytes: {total_incoming} bytes ({total_incoming_gb:.2f} GB)")
    logger.info(f"Total Connections: {total_connections}")
    logger.info(f"Total Duration: {total_duration} seconds")
    send_photo_to_telegram(output_file, f'{VPSFLAG}: Report for {current_time} Outgoing Bytes: {total_outgoing_gb:.2f} GB Incoming Bytes: {total_incoming_gb:.2f} GB Connections: {total_connections} Duration: {total_duration} seconds')

def read_data_from_db():
    """Reads data from the PostgreSQL database and stores it."""
    global data_storage, data_storage_month

    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = connection.cursor()

        # Get today's date
        today = datetime.now().date()
        start_of_month = today.replace(day=1)

        # Read daily data
        cursor.execute("""SELECT username, SUM(bytes_out), SUM(bytes_in), COUNT(*), SUM(duration) FROM user_sessions WHERE disconnect_time >= %s GROUP BY username """, (today,))
        daily_data = cursor.fetchall()
        for username, outgoing_count, incoming_count, connections, duration in daily_data:
            if username not in data_storage:
                data_storage[username] = {'outgoing': 0, 'incoming': 0, 'connections': 0, 'duration': 0}
            data_storage[username]['outgoing'] += outgoing_count
            data_storage[username]['incoming'] += incoming_count
            data_storage[username]['connections'] += connections
            data_storage[username]['duration'] += duration

        # Read monthly data
        cursor.execute("""SELECT username, SUM(bytes_out), SUM(bytes_in), COUNT(*), SUM(duration) FROM user_sessions WHERE disconnect_time >= %s GROUP BY username""", (start_of_month,))
        monthly_data = cursor.fetchall()
        for username, outgoing_count, incoming_count, connections, duration in monthly_data:
            if username not in data_storage_month:
                data_storage_month[username] = {'outgoing': 0, 'incoming': 0, 'connections': 0, 'duration': 0}
            data_storage_month[username]['outgoing'] += outgoing_count
            data_storage_month[username]['incoming'] += incoming_count
            data_storage_month[username]['connections'] += connections
            data_storage_month[username]['duration'] += duration

    except Exception as e:
        logger.error(f"Error reading data from database: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

def create_report():
    """Creates a report and sends it to Telegram."""
    global data_storage, data_storage_month

    logger.info("create_report: Start")
    read_data_from_db()

    users = list(data_storage.keys())
    outgoing_bytes = [data_storage[user]['outgoing'] for user in users]
    incoming_bytes = [data_storage[user]['incoming'] for user in users]
    connections = [data_storage[user]['connections'] for user in users]
    durations = [data_storage[user]['duration'] for user in users]
    create_and_send_chart(users, outgoing_bytes, incoming_bytes, connections, durations)

    # Clear data_storage after sending report
    data_storage.clear()
    logger.info("Cleared data_storage after report.")

def create_report_mon():
    """Creates a report and sends it to Telegram."""
    global data_storage_month

    logger.info("create_report_mon: Start")
    if datetime.now().day == 1:
        users = list(data_storage_month.keys())
        outgoing_bytes = [data_storage_month[user]['outgoing'] for user in users]
        incoming_bytes = [data_storage_month[user]['incoming'] for user in users]
        connections = [data_storage_month[user]['connections'] for user in users]
        durations = [data_storage_month[user]['duration'] for user in users]
        create_and_send_chart(users, outgoing_bytes, incoming_bytes, connections, durations)

        # Clear data_storage_month after sending report
        data_storage_month.clear()
        logger.info("Cleared data_storage_month after report.")

def create_database_if_not_exists():
    """Creates the database if it does not exist."""
    connection = None
    try:
        connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        connection.autocommit = True
        cursor = connection.cursor()

        # Check if the database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info(f"Database {DB_NAME} has been created.")
        else:
            logger.info(f"Database {DB_NAME} already exists.")

    except Exception as e:
        logger.error(f"Error while creating the database: {e}")

    finally:
        if connection:
            cursor.close()
            connection.close()

def scheduled_task():
    """Scheduled task."""
    logger.info("scheduled_task: Start")
    logger.info(f"Current mode: {'TEST_MODE'}")
    if TEST_MODE.lower() == "true":
        schedule.every(30).seconds.do(create_report)
        schedule.every(30).seconds.do(create_report_mon)
    else:
        schedule.every().day.at("12:00").do(create_report)
        schedule.every().day.at("12:00").do(create_report_mon)
    while True:
        try:
            logger.info("scheduled_task: while")
            schedule.run_pending()
            time.sleep(SCHEDULED_TASK_DELAY)
        except Exception as e:
            logger.error(f"Error in scheduled task: {e}")

def main():
    """Main function."""
    log_file_path = os.path.join(DIRECTORY, 'log.app')
    logging.basicConfig(
        filename=log_file_path,
        format='%(asctime)s %(message)s',
        level=logging.DEBUG,
        encoding='utf-8'
    )

    logger.setLevel(logging.DEBUG)
    logger.info("Starting BOT")

    create_database_if_not_exists()
    scheduled_task()

if __name__ == "__main__":
    main()

