#!/usr/bin/env sh
# board-sync dispatch: doctor (offline correctness gate) | sync (live fetch -> canonical).
set -e
case "${1:-doctor}" in
  doctor) exec python doctor.py ;;
  sync)   exec python sync.py ;;
  *) echo "usage: board-sync [doctor|sync]"; exit 2 ;;
esac
