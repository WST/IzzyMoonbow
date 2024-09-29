# Use Python 3.12 slim image as the base (this is already amd64 by default on most systems)
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir cryptography

# Make the startup script executable
RUN chmod +x start.sh

# Expose the port the app runs on
EXPOSE 5000

# Run the startup script when the container launches
CMD ["./start.sh"]
