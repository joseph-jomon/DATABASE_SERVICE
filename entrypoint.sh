#!/bin/bash
set -e

# Set the correct permissions for the secret file
chmod 600 /run/secrets/elastic_password

# Execute the original entrypoint
exec /usr/local/bin/docker-entrypoint.sh "$@"