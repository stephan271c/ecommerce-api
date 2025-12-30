FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY README.md .

# Install dependencies
RUN uv pip install --system -e .

# Copy source code
COPY src/ ./src/

# Expose port (Railway assigns dynamically via $PORT)
EXPOSE 8000

# Default PORT for local development, Railway overrides this
ENV PORT=8000

# Run the application with dynamic port
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port $PORT"]
