FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment variables
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

# Expose port
EXPOSE 5051

# Run with Gunicorn (production server)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5051", "server:app"]
