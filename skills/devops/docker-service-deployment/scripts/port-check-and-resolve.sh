#!/bin/bash
# Port Conflict Detection and Resolution Script
# Usage: ./port-check-and-resolve.sh <port>

set -euo pipefail

PORT=${1:-59000}
VERBOSE=${VERBOSE:-false}

echo "[1/4] Checking if port $PORT is currently in use..."

# Find process using this port
if lsof -i :$PORT &>/dev/null; then
    echo "⚠️  Port $PORT is occupied by:"
    lsof -i :$PORT || true
    READ_YEAH_NO=$(printf "yYnN" | tr '[:upper:]' '[:lower:]')
    read -p "Kill process and free port? (y/n): " -r confirm
    case "$confirm" in
        [Yy]|[Yy][Ee][Ss])
            echo "[2/4] Terminating processes on port $PORT..."
            sudo fuser -k $PORT/tcp || true
            echo "[3/4] Verifying port is now free..."
            if ss -tuln | grep -q ":$PORT "; then
                echo "❌ Port still in use after kill attempt"
                exit 1
            else
                echo "✅ Port $PORT is now available"
            fi
            ;;
        *)
            echo "❌ User declined to free port, exiting"
            exit 1
            ;;
    esac
else
    echo "✅ Port $PORT is available"
fi

echo "[4/4] Port readiness confirmed for deployment"
exit 0