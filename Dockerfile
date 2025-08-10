# Stage 1: Build the dependencies
FROM python:3.11-slim as builder

# Install Poetry
WORKDIR /opt/poetry
RUN pip install poetry==1.8.2

# Copy only the dependency files
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Export the dependencies to a requirements.txt file
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# Stage 2: Build the final application image
FROM python:3.11-slim

WORKDIR /app

# Copy the requirements.txt from the builder stage
COPY --from=builder /app/requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project code into the image
COPY . .

# --- THIS IS THE FINAL, GUARANTEED FIX ---
# This command installs your project (the 'src' directory) as a package.
# This makes all imports like 'from src.bot...' work reliably from anywhere.
RUN pip install -e .
# ----------------------------------------
