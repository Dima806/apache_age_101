#!/usr/bin/env bash
# Install a LOCAL PostgreSQL and build the matching Apache AGE from source.
# Local only: no cloud, no managed service, no account, no API key.
#
# No interactive password. In Codespaces sudo is passwordless only when running AS
# ROOT (`codespace ALL=(root) NOPASSWD:ALL`), so this script never uses
# `sudo -u postgres` (which would prompt). It reaches the postgres role via
# `sudo su - postgres` (root -> postgres needs no password) for the one-time
# bootstrap, then connects over TCP as the project does.
#
# AGE targets specific Postgres majors, so PG_MAJOR and AGE_BRANCH are pinned and
# must match. A zero-build alternative is the official image:  docker run apache/age
#
# One-time step (a few minutes). Re-running is safe.
set -euo pipefail

PG_MAJOR="${PG_MAJOR:-16}"
AGE_BRANCH="${AGE_BRANCH:-PG16}"          # apache/age branch matching PG_MAJOR
AGE_REPO="https://github.com/apache/age.git"
BUILD_DIR="${BUILD_DIR:-/tmp/apache-age-build}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# Connection the project uses (keep in sync with config/settings.yaml / AGE_DB_*).
PG_HOST="${AGE_DB_HOST:-localhost}"
PG_PORT="${AGE_DB_PORT:-5432}"
PG_USER="${AGE_DB_USER:-postgres}"
PG_PASSWORD="${AGE_DB_PASSWORD:-postgres}"
PG_DB="${AGE_DB_DBNAME:-age101}"

echo "==> Installing PostgreSQL ${PG_MAJOR} and build tools (apt; sudo runs as root)"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    "postgresql-${PG_MAJOR}" "postgresql-server-dev-${PG_MAJOR}" \
    build-essential bison flex git libreadline-dev zlib1g-dev

PG_CONFIG="/usr/lib/postgresql/${PG_MAJOR}/bin/pg_config"

echo "==> Verifying Postgres/AGE version compatibility"
"${PG_CONFIG}" --version

echo "==> Cloning and building Apache AGE (branch ${AGE_BRANCH})"
rm -rf "${BUILD_DIR}"
git clone --depth 1 --branch "${AGE_BRANCH}" "${AGE_REPO}" "${BUILD_DIR}"
make -C "${BUILD_DIR}" PG_CONFIG="${PG_CONFIG}"
sudo make -C "${BUILD_DIR}" PG_CONFIG="${PG_CONFIG}" install

echo "==> Starting the local PostgreSQL service"
sudo service postgresql start

echo "==> Bootstrapping role and database (as postgres, no password prompt)"
# sudo -> root (passwordless), then su -> postgres (root needs no password).
# This sets the postgres password to match the config so the project can connect
# over TCP, and creates the database if it is missing.
sudo su - postgres -s /bin/bash <<EOF
set -e
psql -v ON_ERROR_STOP=1 -c "ALTER USER ${PG_USER} PASSWORD '${PG_PASSWORD}';"
psql -tAc "SELECT 1 FROM pg_database WHERE datname='${PG_DB}'" | grep -q 1 \
    || createdb "${PG_DB}"
EOF

echo "==> Enabling the AGE extension over TCP (the same path psycopg uses)"
PGPASSWORD="${PG_PASSWORD}" psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" \
    -d "${PG_DB}" -v ON_ERROR_STOP=1 -f "${HERE}/init_db.sql"

echo "✅ Local Postgres ${PG_MAJOR} with Apache AGE ready (database: ${PG_DB})."
echo "   No cloud, no account. Override the connection with AGE_DB_* env vars."
