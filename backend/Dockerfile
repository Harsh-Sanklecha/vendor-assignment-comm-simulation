# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application files
COPY app/ .

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
