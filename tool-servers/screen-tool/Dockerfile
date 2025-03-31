FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Configure Poetry to not create a virtual environment inside the container
RUN poetry config virtualenvs.create false

# Copy dependency definition files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-dev --no-interaction

# Copy application code
COPY . .

# Expose port for API
EXPOSE 8002

# Run the application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
