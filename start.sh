#!/bin/bash
# 🚀 Komplett PressReader System Starter

echo "🚀 Startar PressReader System..."
echo "=================================="

# Kontrollera om vi är i rätt mapp
if [ ! -f "pressreader_userscript.js" ]; then
    echo "❌ Fel mapp! Kör från PressReader_Extension_Latest/"
    exit 1
fi

# Kontrollera Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 saknas! Installera Python först."
    exit 1
fi

# Installera dependencies om det behövs
echo "📦 Kontrollerar dependencies..."
python3 -c "import fastapi, uvicorn, dotenv" 2>/dev/null || {
    echo "📦 Installerar dependencies..."
    pip3 install fastapi uvicorn python-dotenv watchdog
}

# Kontrollera .env
if [ ! -f ".env" ]; then
    echo "❌ .env fil saknas!"
    echo "🔧 Kör först: python3 setup_api.py"
    exit 1
fi

# Kontrollera API-nycklar
if grep -q "demo_key_replace_with_real" .env; then
    echo "⚠️  DEMO MODE AKTIVT"
    echo "📋 Läs API_KEYS_INSTRUCTIONS.md för att aktivera production mode"
    echo ""
    
    # Starta API-nyckel övervakare i bakgrunden
    echo "👀 Startar API-nyckel övervakare..."
    python3 auto_update_api_keys.py &
    WATCHER_PID=$!
    
    echo "💡 Systemet övervaker .env och aktiverar production mode automatiskt"
    echo "   när du lägger in riktiga API-nycklar"
    echo ""
else
    echo "✅ Production mode aktiv med riktiga API-nycklar"
fi

# Starta servern
echo "🌐 Startar PressReader API Server på http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 Tryck Ctrl+C för att stoppa servern"
echo "=================================="

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stoppar servrar..."
    if [ ! -z "$WATCHER_PID" ]; then
        kill $WATCHER_PID 2>/dev/null
    fi
    exit 0
}

# Sätt upp cleanup vid Ctrl+C
trap cleanup SIGINT SIGTERM

# Starta servern
python3 complete_server.py

# Cleanup vid normal avslutning
cleanup