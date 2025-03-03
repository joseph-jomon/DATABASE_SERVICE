#!/bin/bash
set -e

# Copy the secret file to a writable location
cp /run/secrets/elastic_password /usr/share/elasticsearch/config/elastic_password

# Set the correct permissions for the copied secret file
chmod 600 /usr/share/elasticsearch/config/elastic_password

# Update the environment variable to point to the new location
export ELASTIC_PASSWORD_FILE=/usr/share/elasticsearch/config/elastic_password

# Execute the original entrypoint
exec /usr/local/bin/docker-entrypoint.sh "$@"