#!/bin/bash
# Script to fix the version line in docker-compose.yml

# Remove the 'version' line from docker-compose.yml
sed -i.bak '/^version:/d' docker-compose.yml && rm docker-compose.yml.bak

echo "Removed 'version:' line from docker-compose.yml"
