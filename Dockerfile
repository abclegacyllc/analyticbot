# Use a standard Python 3.11 base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install pipx and use it to install the correct version of poetry
RUN apt-get update && apt-get install -y pipx \
    && pipx install poetry==1.8.2 \
    && apt-get clean

# Add poetry to the system's PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy the dependency files first
# This layer is cached by Docker, speeding up future builds
COPY poetry.lock pyproject.toml ./

# Install the project dependencies using the new, correct Poetry version
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of your application code
COPY . .

# The command to run when the container starts
# This will be overridden by your docker-compose.yml, which is correct
CMD ["python", "run_bot.py"]
