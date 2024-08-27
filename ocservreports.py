#!/usr/bin/env python3
import os
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from datetime import datetime
import schedule
import time
import requests
import logging

TOKEN = os.getenv('TOKEN')
GROUP_CHAT_ID = os.getenv('CHAT_ID')
DIRECTORY = os.getenv('DIRECTORY')
SCHEDULED_TASK_DELAY = 60  # Sec

# Set the logging level for matplotlib to WARNING to suppress unnecessary messages
matplotlib_logger = logging.getLogger('matplotlib')
matplotlib_logger.setLevel(logging.WARNING)
logger = logging.getLogger('my_report_logging')
data_storage = {}
data_storage_month = {}

def send_photo_to_telegram(photo_path, caption):
    """Sends a photo to the Telegram chat."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': GROUP_CHAT_ID, 'caption': caption}
        response = requests.post(url, data=data, files=files)
        if response.status_code != 200:
            logger.error(f"Failed to send photo: {response.text}")

def update_mon_logs():
    """Updates each .mon.log file with data from data_storage_month."""
    global data_storage, data_storage_month

    for user, values in data_storage_month.items():
        filename = os.path.join(DIRECTORY, f"{user}.mon.log")
        with open(filename, 'w') as file:
            file.write(f"{values['outgoing']}\n")
            file.write(f"{values['incoming']}\n")
        logger.info(f"Updated {filename} with outgoing: {values['outgoing']} and incoming: {values['incoming']}")

def create_and_send_chart(users, outgoing_bytes, incoming_bytes):
    """Creates and sends a chart of data usage."""

    plt.title('Кто сколько съел')
#    bar_width = 0.35
#    x = range(len(users))

#    plt.figure(figsize=(10, 5))
#    plt.bar(x, outgoing_bytes, width=bar_width, color='#D5006D', label='Outgoing')
#    plt.bar([p + bar_width for p in x], incoming_bytes, width=bar_width, color='#FFD700', label='Incoming')

#    plt.xlabel('Человеки')
#    plt.ylabel('Количество')
#    plt.xticks([p + bar_width / 2 for p in x], users)
#    plt.grid(axis='y', linestyle='--', alpha=0.7)
#    plt.legend()


    num_users = len(users)
    colors = cm.get_cmap('rainbow', num_users)
    step = num_users // max(len(users), 1)  # Step for selecting colors
    selected_colors = [colors(i * step) for i in range(max(len(users), 1))]

    # Create the first pie chart for outgoing traffic
    plt.figure(figsize=(15, 12))

    plt.subplot(1, 2, 1)  # First chart
    wedges, texts, autotexts = plt.pie(outgoing_bytes, autopct='%1.1f%%', startangle=90, colors=selected_colors, textprops=dict(color="black"))
    plt.title('User Share in Outgoing Traffic')
    plt.axis('equal')  # To make the pie chart circular
    plt.legend(wedges, users, title="Users", loc="lower center", ncol=1)

    # Create the second pie chart for incoming traffic
    plt.subplot(1, 2, 2)  # Second chart
    wedges, texts, autotexts = plt.pie(incoming_bytes, autopct='%1.1f%%', startangle=90, colors=selected_colors, textprops=dict(color="black"))
    plt.title('User Share in Incoming Traffic')
    plt.axis('equal')  # To make the pie chart circular
    plt.legend(wedges, users, title="Users", loc="lower center", ncol=1)

    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)

    output_file = os.path.join(DIRECTORY, 'bytes_usage.png')
    plt.savefig(output_file)
    plt.close()

    # Get date
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Calculate total outgoing and incoming bytes
    total_outgoing = sum(outgoing_bytes)
    total_incoming = sum(incoming_bytes)
    # Convert bytes to gigabytes
    total_outgoing_gb = total_outgoing / (1024 ** 3)
    total_incoming_gb = total_incoming / (1024 ** 3)
    # Log the total bytes in gigabytes
    logger.info(f"Total Outgoing Bytes: {total_outgoing} bytes ({total_outgoing_gb:.2f} GB)")
    logger.info(f"Total Incoming Bytes: {total_incoming} bytes ({total_incoming_gb:.2f} GB)")
    send_photo_to_telegram(output_file, f'Report for {current_time} Outgoing Bytes: {total_outgoing_gb:.2f} GB Incoming Bytes: {total_incoming_gb:.2f} GB')

def read_data_from_files(extension, storage):
    """Reads data from files with the specified extension and stores it."""
    for filename in os.listdir(DIRECTORY):
        if filename.endswith(extension):
            user = filename[:-len(extension)]
            with open(os.path.join(DIRECTORY, filename), 'r') as file:
                try:
                    outgoing_count = int(file.readline().strip())
                    incoming_count = int(file.readline().strip())
                    if user not in storage:
                        storage[user] = {'outgoing': 0, 'incoming': 0}
                    storage[user]['outgoing'] += outgoing_count
                    storage[user]['incoming'] += incoming_count
                except ValueError:
                    logger.error(f"Error reading data from file {filename}")

        with open(filename, 'w') as file:
                file.truncate(0)

def create_report():
    """Creates a report and sends it to Telegram."""
    global data_storage, data_storage_month

    logger.info("create_report: Start")
    read_data_from_files('.day.log', data_storage)

    for user, values in data_storage.items():
        if user not in data_storage_month:
            data_storage_month[user] = {'outgoing': 0, 'incoming': 0}
        data_storage_month[user]['outgoing'] += values['outgoing']
        data_storage_month[user]['incoming'] += values['incoming']

    read_data_from_files('.mon.log', data_storage_month)

    # Log the contents of data_storage and data_storage_month
    logger.info(f"Data Storage: {data_storage}")
    logger.info(f"Data Storage Month: {data_storage_month}")

    update_mon_logs()

    users = list(data_storage.keys())
    outgoing_bytes = [data_storage[user]['outgoing'] for user in users]
    incoming_bytes = [data_storage[user]['incoming'] for user in users]
    create_and_send_chart(users, outgoing_bytes, incoming_bytes)

def create_report_mon():
    """Creates a report and sends it to Telegram."""
    global data_storage_month

    logger.info("create_report_mon: Start")
    if datetime.now().day == 1:
        users = list(data_storage_month.keys())
        outgoing_bytes = [data_storage_month[user]['outgoing'] for user in users]
        incoming_bytes = [data_storage_month[user]['incoming'] for user in users]
        create_and_send_chart(users, outgoing_bytes, incoming_bytes)

def scheduled_task():
    """Scheduled task."""
    logger.info("scheduled_task: Start")
    #schedule.every(10).seconds.do(create_report)
    schedule.every().day.at("12:00").do(create_report)
    schedule.every().day.at("12:00").do(create_report_mon)
    while True:
        logger.info("scheduled_task: while")
        schedule.run_pending()
        time.sleep(SCHEDULED_TASK_DELAY)

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
    scheduled_task()

if __name__ == "__main__":
    main()
