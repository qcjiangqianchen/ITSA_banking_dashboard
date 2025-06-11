# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5002 available to the world outside this container
EXPOSE 5004

# Define environment variables
ENV FLASK_APP=log.py
ENV FLASK_ENV=production

# Run flask when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=5004"]
