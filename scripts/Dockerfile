# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app
COPY requirements.txt .
COPY ocservaddentry.py .
COPY ocservgetentry.py .
COPY testdb.py .

# Install dependencies for creating a virtual environment
RUN apt-get update && apt-get install -y  build-essential python3-venv libpq-dev

# Create a virtual environment
RUN python3 -m venv venv

# Activate the virtual environment, upgrade pip, and install dependencies
RUN . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]

