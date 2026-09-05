#!/bin/bash
# stop.sh — Detiene el Corrector EOI B2 y el tunnel
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "⏹  Deteniendo Corrector EOI B2..."

if [ -f "$APP_DIR/.streamlit_pid" ]; then
    PID=$(cat "$APP_DIR/.streamlit_pid")
    kill "$PID" 2>/dev/null && echo "  ✅ Streamlit detenido (PID $PID)" || echo "  ⚠️  PID $PID no encontrado"
    rm -f "$APP_DIR/.streamlit_pid"
fi

if [ -f "$APP_DIR/.tunnel_pid" ]; then
    PID=$(cat "$APP_DIR/.tunnel_pid")
    kill "$PID" 2>/dev/null && echo "  ✅ Tunnel detenido (PID $PID)" || echo "  ⚠️  PID $PID no encontrado"
    rm -f "$APP_DIR/.tunnel_pid"
fi

# Kill any remaining processes on port 8502
fuser -k 8502/tcp 2>/dev/null || true
echo "✅ Listo."
