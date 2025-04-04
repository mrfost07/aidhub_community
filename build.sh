#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Create static directory if it doesn't exist
mkdir -p static

# Go to the Django project directory
cd aidhub

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
