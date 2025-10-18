# Use Python 3.11 for compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -r botuser && \
    chown -R botuser:botuser /app
USER botuser

# Run the bot
CMD ["python", "main.py"]