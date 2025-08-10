#!/bin/sh

# This script ensures the Python path is set correctly,
# then executes the command passed to it.

# Set the PYTHONPATH to the application root
export PYTHONPATH=/app

# Execute the command that was passed to this script
exec "$@"
