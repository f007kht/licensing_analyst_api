# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'app' directory into the container at /app/app
COPY app/ app/

# Expose the port your FastAPI app runs on
EXPOSE 8000

# Command to run the application
# Use 0.0.0.0 to bind to all network interfaces, and 8000 as the internal container port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
