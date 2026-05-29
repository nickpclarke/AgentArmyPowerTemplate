"""Infisical doctor (ARC-ADR-037) — proves the backend is up, migrated, and reachable:
GET http://localhost:8333/api/status must return 200. The host port is a localhost
loopback to the operator's own container, so the http:// findings below do not apply."""
import sys
import urllib.request

URL = "http://localhost:8333/api/status"  # nosemgrep


def main() -> int:
    try:
        with urllib.request.urlopen(URL, timeout=10) as r:  # nosemgrep
            code = r.status
    except Exception as e:
        print(f"[FAIL] {URL}: {e}")
        return 1
    print(f"[{'PASS' if code == 200 else 'FAIL'}] {URL} -> {code}")
    return 0 if code == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
