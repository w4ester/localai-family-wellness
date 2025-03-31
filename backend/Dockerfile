# Dockerfile (Located inside the ./backend directory)
# Defines the image for the main FastAPI backend and Celery workers

# --- Base Stage ---
# Use an official Python runtime as a parent image
FROM python:3.11-slim as base

# Set environment variables for Python behavior and Poetry version
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.7.1

# Install essential system dependencies needed for building Python packages
# Add others if required by your specific dependencies (e.g., libraries for image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry itself using pip
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Configure Poetry to install packages into the main system site-packages
# instead of creating a separate virtual environment inside the container.
RUN poetry config virtualenvs.create false

# Set the working directory within the container
WORKDIR /app

# --- Builder Stage ---
# This stage installs dependencies, leveraging Docker cache.
# It helps keep the final image smaller by not including build tools if using multi-stage,
# though this example remains single-stage for simplicity with `virtualenvs.create false`.
FROM base as builder

# Copy both dependency definition files
COPY pyproject.toml poetry.lock* requirements.txt* /app/

# Try to install with Poetry first, if not use pip with requirements.txt
RUN if [ -f pyproject.toml ]; then \
        echo "Installing with Poetry" && \
        poetry install --no-interaction --no-ansi --no-root --sync || \
        (echo "Poetry install failed, falling back to pip" && \
         pip install --no-cache-dir -r requirements.txt && \
         touch /app/INSTALLED_WITH_PIP); \
    else \
        echo "No pyproject.toml found, using pip" && \
        pip install --no-cache-dir -r requirements.txt && \
        touch /app/INSTALLED_WITH_PIP; \
    fi

# --- Final Runtime Stage ---
# Start fresh from the base to potentially have a smaller final image,
# although with `virtualenvs.create false` the benefit is less pronounced
# than with multi-stage builds using virtualenvs.
FROM base as final

# Copy the installed packages from the builder stage's site-packages
# Note: With `virtualenvs.create false`, packages are in the global site-packages.
# We need to determine the exact path. A common path is /usr/local/lib/python3.11/site-packages
# This step might be optional if just copying the whole app directory below is sufficient,
# but explicit copying can sometimes be cleaner. Let's simplify for now.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/INSTALLED_WITH_PIP* /app/

# Copy the application code from the build context's current directory (.)
# into the container's /app directory. Respects .dockerignore.
# This assumes the Docker build context is set to './backend' in docker-compose.yml.
# Since WORKDIR is /app, '.' copies into /app.
COPY . /app/

# Display which installation method was used
RUN if [ -f /app/INSTALLED_WITH_PIP ]; then \
        echo "Dependencies were installed with pip"; \
    else \
        echo "Dependencies were installed with Poetry"; \
    fi

# Inform Docker that the container listens on port 8000 at runtime.
EXPOSE 8000

# Default command to run the FastAPI application using Uvicorn.
# This is suitable for DEVELOPMENT due to `--reload`.
# Override this command in production (e.g., via docker-compose.override.yml or separate prod Dockerfile/stage).
# It correctly references 'app.main:app' based on your backend/app/main.py structure.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Example Production CMD (Commented out) ---
# For production, remove '--reload' and potentially add '--workers'.
# The number of workers depends on your server resources (often 2*CPU cores + 1).
# CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]