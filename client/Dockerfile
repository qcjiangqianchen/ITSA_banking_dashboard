# Use the official Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=client.py
ENV FLASK_RUN_HOST=0.0.0.0

# Copy the rest of the application files into the container
COPY . .

# Expose the port your app runs on (default Flask port is 5000)
EXPOSE 5001

# Set environment variables (optional, use .env for sensitive data)
ENV FLASK_ENV=production

CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]