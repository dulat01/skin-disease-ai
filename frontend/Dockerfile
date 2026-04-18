FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask requests gunicorn

# Copy application
COPY . .

# Environment
ENV FLASK_APP=app.py
ENV BACKEND_URL=http://api-gateway:8000

# Expose port
EXPOSE 3000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "4", "app:app"]
