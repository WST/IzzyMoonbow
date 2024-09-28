# Use Python 3.12 slim image as the base
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies required for cryptography and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    supervisor

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install cryptography
RUN pip install --no-cache-dir cryptography

# Copy Supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME IzzyMoonbow

# Run Supervisor when the container launches
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
