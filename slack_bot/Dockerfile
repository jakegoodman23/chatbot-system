FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r slackbot && useradd -r -g slackbot slackbot
RUN chown -R slackbot:slackbot /app
USER slackbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import aiohttp; import asyncio; asyncio.run(aiohttp.ClientSession().get('http://localhost:8000/health').close())" || exit 1

# Run the enhanced Slack bot by default
CMD ["python", "enhanced_slack_bot.py"]