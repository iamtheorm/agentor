FROM python:3.11.8-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies, PostgreSQL, and Redis
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql \
    postgresql-contrib \
    redis-server \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Setup PostgreSQL user and database
USER postgres
RUN /etc/init.d/postgresql start && \
    psql --command "CREATE USER db_user WITH SUPERUSER PASSWORD 'db_password';" && \
    createdb -O db_user app_db
USER root

# Configure Redis to run in background (daemonize)
RUN sed -i 's/^daemonize no/daemonize yes/' /etc/redis/redis.conf

# Set up working directory
WORKDIR /app

# Install Python dependencies
COPY repo/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY repo/ .

# Copy verifier tests
COPY verifier/ /app/verifier/

# Copy entrypoint
COPY environment/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose ports (although this might be run with --network none for eval, useful for local debugging)
EXPOSE 8000 5432 6379

ENTRYPOINT ["/app/entrypoint.sh"]
