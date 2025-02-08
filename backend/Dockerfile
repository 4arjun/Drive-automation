# Use an official Python runtime as base image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy project files
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Gunicorn will run on
EXPOSE 8080

# Run Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "backend.wsgi:application"]
