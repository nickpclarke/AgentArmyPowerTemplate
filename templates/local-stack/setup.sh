#!/usr/bin/env bash
# AgentArmy local-stack — generate dev secrets, build the images, bring
# everything up, then run the doctor. Idempotent: re-running is safe and
# reuses existing secrets.
set -euo pipefail

# Git Bash on Windows mangles /run/secrets/* paths when calling docker.exe.
# Harmless no-op on Linux/macOS.
export MSYS_NO_PATHCONV=1

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"

mode="${1:-up}"

if [ "$mode" = "--down" ] || [ "$mode" = "down" ]; then
  echo "=== DOWN (keeping volumes — pass --wipe to also drop data) ==="
  docker compose down
  exit 0
fi
if [ "$mode" = "--wipe" ] || [ "$mode" = "wipe" ]; then
  echo "=== WIPE (down + drop all volumes — destroys local data) ==="
  docker compose down --volumes
  exit 0
fi

mkdir -p .secrets

# Generate one dev secret if missing. Stored as a single line (no trailing
# newline) — docker secret files are read verbatim, and pg / arcadedb both
# choke on trailing whitespace in passwords.
#
# Implementation: dd a fixed 96-byte chunk from /dev/urandom (no pipe-close
# race that Git Bash mishandles), filter to alnum, take 32 chars. 96 random
# bytes yields ~60 alnum chars on average — well above the 32 we need.
gen_secret() {
  local file=".secrets/$1.txt"
  if [ ! -s "$file" ]; then
    LC_ALL=C dd if=/dev/urandom bs=96 count=1 2>/dev/null \
      | LC_ALL=C tr -dc 'A-Za-z0-9' \
      | head -c 32 > "$file"
    echo "  generated $file"
  fi
}

echo "=== preparing .secrets/ ==="
gen_secret arcadedb_root_password
gen_secret arcadedb_password
gen_secret postgres_password
gen_secret github_webhook_secret
gen_secret fuseki_admin_password

# .gitignore lives next to the secrets — never let the .txt files escape.
cat > .secrets/.gitignore <<'EOF'
*.txt
!README.md
EOF

echo
echo "=== building all 5 services ==="
docker compose build

echo
echo "=== bringing the stack up (compose up -d --wait) ==="
docker compose up -d --wait

echo
echo "=== running local-stack doctor ==="
bash "$here/local-stack-doctor.sh" || {
  echo
  echo "doctor failed — leaving the stack running so you can poke at it."
  echo "logs:   docker compose logs --tail=80"
  echo "down:   $0 --down       (keep data)"
  echo "wipe:   $0 --wipe       (drop volumes)"
  exit 1
}

cat <<EOF

══════════════════════════════════════════════════════════════════════════
  AgentArmy local-stack is UP. Endpoints:

    ArcadeDB Studio    http://localhost:2480
    Postgres (DBOS)    postgresql://dbos@localhost:5432/dbos_system
    NATS client        nats://localhost:4222   (monitor http://localhost:8222)
    Event-bridge       http://localhost:8080/healthz
    Fuseki + SHACL     http://localhost:3030

  Down (keep data):   $0 --down
  Wipe (drop data):   $0 --wipe
══════════════════════════════════════════════════════════════════════════
EOF
