#!/bin/bash
# PressReader API Server Starter

echo "🚀 Startar PressReader API Server..."

# Kontrollera om .env existerar
if [ ! -f .env ]; then
    echo "❌ .env fil saknas!"
    echo "📖 Kör först: python setup_api.py"
    exit 1
fi

# Kontrollera om API-nycklar är konfigurerade
if grep -q "your_api_key_here" .env; then
    echo "⚠️  API-nycklar behöver konfigureras i .env"
    echo "📖 Följ instruktionerna i setup_pressreader_api.md"
    exit 1
fi

# Starta servern
echo "✅ Startar server på http://localhost:8000"
python pressreader_enhanced_server.py
