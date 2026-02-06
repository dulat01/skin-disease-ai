#!/bin/bash
# =============================================================================
# PostgreSQL Multiple Database Initialization Script
# Creates separate databases for each microservice
# =============================================================================

set -e
set -u

function create_database() {
    local database=$1
    echo "Creating database '$database'..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        SELECT 'CREATE DATABASE $database'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$database')\gexec
EOSQL
    echo "Database '$database' created successfully!"
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "=== Multiple Database Creation ==="
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_database $db
    done
    echo "=== All databases created ==="
fi
