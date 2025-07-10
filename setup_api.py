#!/usr/bin/env python3
"""
PressReader API Setup Script
Automatisk konfiguration av PressReader API integration
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def install_dependencies():
    """Installera nödvändiga Python-paket"""
    print("📦 Installerar dependencies...")
    
    packages = [
        'python-dotenv',
        'requests',
        'fastapi',
        'uvicorn[standard]',
        'python-multipart'
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installerat")
        except subprocess.CalledProcessError:
            print(f"❌ Fel vid installation av {package}")
            return False
    
    return True

def create_env_template():
    """Skapa .env template"""
    print("📝 Skapar .env template...")
    
    env_content = """# PressReader API Configuration
# Hämta dessa värden från https://developers.pressreader.com

PRESSREADER_API_KEY=your_api_key_here
PRESSREADER_API_SECRET=your_api_secret_here
PRESSREADER_BASE_URL=https://api.prod.pressreader.com
PRESSREADER_DISCOVERY_URL=https://discovery.pressreader.com

# Server Configuration
SERVER_HOST=localhost
SERVER_PORT=8000
DEBUG=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=pressreader_api.log
"""
    
    env_path = Path('.env')
    if not env_path.exists():
        env_path.write_text(env_content)
        print("✅ .env template skapad")
    else:
        print("ℹ️  .env fil existerar redan")
    
    return True

def create_config_file():
    """Skapa API konfigurationsfil"""
    print("⚙️  Skapar API konfiguration...")
    
    config = {
        "api_version": "v2",
        "endpoints": {
            "discovery": "/discovery/search",
            "publications": "/publications",
            "articles": "/articles",
            "auth": "/auth/token"
        },
        "search_settings": {
            "max_results": 20,
            "timeout": 30,
            "retry_attempts": 3
        },
        "swedish_publications": {
            "svd": "Svenska Dagbladet",
            "kungalvsposten": "Kungälvs-Posten",
            "dn": "Dagens Nyheter"
        },
        "userscript_settings": {
            "button_delay": 3000,
            "search_delay": 500,
            "max_search_strategies": 7
        }
    }
    
    config_path = Path('api_config.json')
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    print("✅ API konfiguration skapad")
    
    return True

def check_api_credentials():
    """Kontrollera om API-nycklar är konfigurerade"""
    print("🔑 Kontrollerar API-nycklar...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env fil saknas")
        return False
    
    env_content = env_path.read_text()
    
    if 'your_api_key_here' in env_content:
        print("⚠️  API-nycklar behöver konfigureras i .env")
        print("📖 Följ instruktionerna i setup_pressreader_api.md")
        return False
    
    print("✅ API-nycklar konfigurerade")
    return True

def create_start_script():
    """Skapa start-script för servern"""
    print("🚀 Skapar start-script...")
    
    start_script = """#!/bin/bash
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
"""
    
    start_path = Path('start_server.sh')
    start_path.write_text(start_script)
    
    # Gör scriptet körbart
    try:
        os.chmod(start_path, 0o755)
        print("✅ Start-script skapat: start_server.sh")
    except:
        print("⚠️  Start-script skapat men kunde inte göras körbart")
    
    return True

def print_next_steps():
    """Skriv ut nästa steg"""
    print("\n" + "="*60)
    print("🎉 SETUP KLAR!")
    print("="*60)
    print("\n📋 NÄSTA STEG:")
    print("\n1. 🔑 Konfigurera API-nycklar:")
    print("   - Gå till: https://developers.pressreader.com")
    print("   - Logga in med: isak@allgot.se")
    print("   - Skapa nytt projekt och hämta API-nycklar")
    print("   - Uppdatera .env filen med dina nycklar")
    
    print("\n2. 🚀 Starta servern:")
    print("   ./start_server.sh")
    print("   eller")
    print("   python pressreader_enhanced_server.py")
    
    print("\n3. 🧪 Testa userscriptet:")
    print("   - Gå till en SVD-artikel med paywall")
    print("   - Vänta 3 sekunder")
    print("   - Klicka på grön knapp")
    
    print("\n📖 Läs mer i: setup_pressreader_api.md")
    print("="*60)

def main():
    """Huvudfunktion"""
    print("🔧 PressReader API Setup")
    print("=" * 40)
    
    # Kontrollera att vi är i rätt mapp
    if not Path('pressreader_userscript.js').exists():
        print("❌ Fel mapp! Kör scriptet från PressReader_Extension_Latest/")
        sys.exit(1)
    
    success = True
    
    # Installera dependencies
    if not install_dependencies():
        success = False
    
    # Skapa konfigurationsfiler
    if not create_env_template():
        success = False
    
    if not create_config_file():
        success = False
    
    if not create_start_script():
        success = False
    
    # Kontrollera API-nycklar
    check_api_credentials()
    
    if success:
        print_next_steps()
    else:
        print("\n❌ Setup misslyckades! Kontrollera felmeddelanden ovan.")
        sys.exit(1)

if __name__ == "__main__":
    main()