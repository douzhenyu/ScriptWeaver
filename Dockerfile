FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source
COPY scriptweaver/ scriptweaver/

# Persistence directory
RUN mkdir -p /app/data
VOLUME /app/data

EXPOSE 8000

# Default: Mock mode. Set SCRIPTWEAVER_API_KEY for real LLM.
CMD ["uvicorn", "scriptweaver.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
