#!/usr/bin/env sh
# Stand up Infisical (ARC-ADR-037) locally. Generates a gitignored .env with freshly
# rolled secrets on first run, then brings the stack up. Readiness: python doctor.py.
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "generating .env (rolling fresh secrets) ..."
  ENC=$(openssl rand -hex 16)
  AUTH=$(openssl rand -base64 32)
  PGPW=$(openssl rand -hex 24)
  cat > .env <<EOF
ENCRYPTION_KEY=$ENC
AUTH_SECRET=$AUTH
POSTGRES_USER=infisical
POSTGRES_PASSWORD=$PGPW
POSTGRES_DB=infisical
DB_CONNECTION_URI=postgres://infisical:$PGPW@infisical-db:5432/infisical
REDIS_URL=redis://infisical-redis:6379
SITE_URL=http://localhost:8333
OTEL_TELEMETRY_COLLECTION_ENABLED=false
EOF
  echo ".env created (gitignored)."
fi

docker compose up -d
echo "Infisical starting (DB migrations run on first boot, ~1-2 min)."
echo "  readiness: python doctor.py        UI/API: http://localhost:8333"
