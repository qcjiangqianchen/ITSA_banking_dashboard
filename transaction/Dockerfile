# Use an official Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy all files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5003

# Run the app
CMD ["python", "transaction.py"]
