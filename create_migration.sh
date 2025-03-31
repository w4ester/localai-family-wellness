#!/bin/bash

# Change to the backend directory
cd /Users/willf/smartIndex/epicforesters/localai-family-wellness/backend

# Generate the initial migration
alembic revision --autogenerate -m "Initial schema"

# If the previous command succeeded, apply the migration
if [ $? -eq 0 ]; then
    echo "Migration created successfully. Now applying migration..."
    alembic upgrade head
    echo "Database migration complete."
else
    echo "Failed to create migration. Check the error messages above."
fi
