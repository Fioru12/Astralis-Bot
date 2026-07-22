FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot_telegram.py .

# Run bot
CMD ["python", "bot_telegram.py"]
