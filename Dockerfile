# Stage 1: Build the dependencies
FROM python:3.11-slim as builder

WORKDIR /opt/poetry
RUN pip install poetry==1.8.2

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Stage 2: Build the final application image
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# This command now correctly installs your 'bot' package
RUN pip install -e .
