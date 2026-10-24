#!/bin/bash
# start.sh — Arranque del Corrector EOI B2
# Puerto: 8502 (aislado del sitio principal en 80/443)
# Servidor: solo escucha en 127.0.0.1, expuesto via Cloudflare Tunnel

set -e
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$APP_DIR/.streamlit_pid"
TUNNEL_PID_FILE="$APP_DIR/.tunnel_pid"
LOG_FILE="$APP_DIR/corrector_b2.log"
TUNNEL_LOG="$APP_DIR/tunnel.log"
PORT=8502
export PATH="$HOME/.local/bin:$PATH"

echo "════════════════════════════════════════"
echo "  Corrector EOI B2 — Arranque"
echo "════════════════════════════════════════"

# Stop existing instances
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null && echo "⏹  Instancia anterior detenida (PID $OLD_PID)" || true
    rm -f "$PID_FILE"
fi
if [ -f "$TUNNEL_PID_FILE" ]; then
    OLD_TPID=$(cat "$TUNNEL_PID_FILE")
    kill "$OLD_TPID" 2>/dev/null || true
    rm -f "$TUNNEL_PID_FILE"
fi

cd "$APP_DIR"

# Install dependencies if needed
echo "📦 Verificando dependencias..."
python3 -m pip install --user -q -r requirements.txt

# Start Streamlit (background, localhost only)
echo "🚀 Iniciando Streamlit en 127.0.0.1:$PORT..."
nohup python3 -m streamlit run app.py \
    --server.port=$PORT \
    --server.address=127.0.0.1 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    > "$LOG_FILE" 2>&1 &
STREAMLIT_PID=$!
echo $STREAMLIT_PID > "$PID_FILE"
echo "✅ Streamlit PID: $STREAMLIT_PID"

# Wait for Streamlit to be ready
echo "⏳ Esperando que Streamlit arranque..."
for i in $(seq 1 20); do
    if curl -s -o /dev/null "http://127.0.0.1:$PORT"; then
        echo "✅ Streamlit listo."
        break
    fi
    sleep 1
done

# Start Cloudflare Quick Tunnel (no config needed)
echo ""
echo "🌐 Iniciando Cloudflare Tunnel..."
if ! command -v cloudflared &> /dev/null; then
    echo "⚠️  cloudflared no encontrado. Instalando..."
    # Hosting compartido sin sudo: binario oficial en ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    if curl -fsSL -o "$HOME/.local/bin/cloudflared"         https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; then
        chmod +x "$HOME/.local/bin/cloudflared"
    else
        echo "❌ No se pudo descargar cloudflared."
        echo "   La app está disponible LOCALMENTE en: http://127.0.0.1:$PORT"
        exit 1
    fi
fi

# Launch tunnel and capture URL
nohup cloudflared tunnel --url "http://127.0.0.1:$PORT" > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!
echo $TUNNEL_PID > "$TUNNEL_PID_FILE"

echo "⏳ Esperando URL pública del tunnel..."
PUBLIC_URL=""
for i in $(seq 1 30); do
    PUBLIC_URL=$(grep -oP 'https://[a-z0-9\-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
    if [ -n "$PUBLIC_URL" ]; then
        break
    fi
    sleep 1
done

echo ""
echo "════════════════════════════════════════"
echo "  ✅ CORRECTOR EOI B2 ACTIVO"
echo "════════════════════════════════════════"
if [ -n "$PUBLIC_URL" ]; then
    echo ""
    echo "  🌐 URL PÚBLICA:  $PUBLIC_URL"
    echo ""
    echo "  🔒 URL LOCAL:    http://127.0.0.1:$PORT"
    echo ""
    echo "  🔑 Contraseña:   la de APP_PASSWORD en .env"
    echo ""
    echo "  📋 PIDs: Streamlit=$STREAMLIT_PID | Tunnel=$TUNNEL_PID"
    echo ""
    echo "  Para detener: bash stop.sh"
    echo "════════════════════════════════════════"
else
    echo ""
    echo "  ⚠️  No se pudo obtener URL pública del tunnel."
    echo "  Revisa el log: $TUNNEL_LOG"
    echo ""
    echo "  🔒 URL LOCAL:  http://127.0.0.1:$PORT"
    echo "════════════════════════════════════════"
fi
