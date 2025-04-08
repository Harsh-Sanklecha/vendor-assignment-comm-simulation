# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application files
COPY app/ .

# Install dependencies
RUN pip install --no-cache-dir streamlit requests

# Command to run the application
CMD ["streamlit", "run", "main.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
