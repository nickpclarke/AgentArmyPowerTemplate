#!/usr/bin/env bash
# AgentArmy SessionStart hook: install the .NET SDK for Claude Code on the web.
#
# The web session runs in an ephemeral container that is recreated fresh each
# time, so the SDK needed to build/test the net10.0 projects under
# templates/middle-core/ has to be installed at session start.
#
# Idempotent (safe to re-run), non-interactive, and remote-only.
set -euo pipefail

# Only run in the remote (web) container. Local machines manage their own SDK.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

DOTNET_CHANNEL="10.0"
DOTNET_DIR="$HOME/.dotnet"

# Persist PATH + opt-outs so dotnet is available for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export DOTNET_ROOT=\"$DOTNET_DIR\""
    echo "export PATH=\"$DOTNET_DIR:\$PATH\""
    echo "export DOTNET_CLI_TELEMETRY_OPTOUT=1"
    echo "export DOTNET_NOLOGO=1"
  } >> "$CLAUDE_ENV_FILE"
fi

export PATH="$DOTNET_DIR:$PATH"

# Skip the download if a 10.x SDK is already present (cached container reuse).
if [ -x "$DOTNET_DIR/dotnet" ] && "$DOTNET_DIR/dotnet" --list-sdks 2>/dev/null | grep -q '^10\.'; then
  echo "SessionStart: .NET 10 SDK already present ($("$DOTNET_DIR/dotnet" --version))"
  exit 0
fi

echo "SessionStart: installing .NET ${DOTNET_CHANNEL} SDK..."
curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh
chmod +x /tmp/dotnet-install.sh
/tmp/dotnet-install.sh --channel "$DOTNET_CHANNEL" --install-dir "$DOTNET_DIR"

echo "SessionStart: .NET SDK ready ($("$DOTNET_DIR/dotnet" --version))"
