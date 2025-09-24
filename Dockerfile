# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose the port Flask/Gunicorn will run on
EXPOSE 8000

# Run with Gunicorn (recommended for production)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
