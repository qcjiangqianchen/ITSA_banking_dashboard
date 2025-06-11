# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Expose port 5020 for the Flask application
EXPOSE 5020

# Set environment variables for Flask
ENV FLASK_APP=admin.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5020

# Run the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5020"]
