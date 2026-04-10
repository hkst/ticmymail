# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "src.tmm.api.http_app:app", "--host", "0.0.0.0", "--port", "8000"]