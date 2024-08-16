# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app
COPY requirements.txt .
COPY ocservreports.py .

# Install dependencies for creating a virtual environment
RUN apt-get update && apt-get install -y python3-venv

# Create a virtual environment
RUN python3 -m venv venv

# Activate the virtual environment, upgrade pip, and install dependencies
RUN . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Command to run your script
CMD ["venv/bin/python", "ocservreports.py"]

