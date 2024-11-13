# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies for Playwright and other required tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gnupg curl libxshmfence1 && \
    apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libx11-xcb1 libcups2 \
    libdbus-glib-1-2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 && \
    rm -rf /var/lib/apt/lists/*

# Install project dependencies without caching
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN playwright install --with-deps chromium

# Expose the port Flask runs on
EXPOSE 5000

# Temporary: Run the container as root to check permissions (remove in production)
USER root

# Run the Flask application
CMD ["python", "main.py"]
