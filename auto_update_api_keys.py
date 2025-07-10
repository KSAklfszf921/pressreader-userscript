#!/usr/bin/env python3
"""
Automatisk API-nyckel uppdaterare
Övervakar när riktiga nycklar läggs till och uppdaterar systemet automatiskt
"""

import os
import time
import json
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Konfigurera logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIKeyWatcher(FileSystemEventHandler):
    """Övervakar förändringar i .env filen"""
    
    def __init__(self):
        self.env_path = Path('.env')
        self.last_check = self.check_api_keys()
        
    def on_modified(self, event):
        """Körs när fil ändras"""
        if event.src_path.endswith('.env'):
            logger.info("📝 .env fil uppdaterad - kontrollerar API-nycklar...")
            new_status = self.check_api_keys()
            
            if new_status != self.last_check:
                if new_status:
                    logger.info("🎉 Riktiga API-nycklar detekterade!")
                    self.activate_production_mode()
                else:
                    logger.info("⚠️  Demo-nycklar detekterade")
                
                self.last_check = new_status
    
    def check_api_keys(self) -> bool:
        """Kontrollera om riktiga API-nycklar finns"""
        try:
            if not self.env_path.exists():
                return False
            
            env_content = self.env_path.read_text()
            
            api_key = None
            api_secret = None
            
            for line in env_content.split('\n'):
                if line.startswith('PRESSREADER_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                elif line.startswith('PRESSREADER_API_SECRET='):
                    api_secret = line.split('=', 1)[1].strip()
            
            # Kontrollera om vi har riktiga nycklar
            demo_values = ['', 'demo_key_replace_with_real', 'demo_secret_replace_with_real', 'your_api_key_here', 'your_api_secret_here']
            
            real_api_key = api_key and api_key not in demo_values
            real_api_secret = api_secret and api_secret not in demo_values
            
            return real_api_key and real_api_secret
            
        except Exception as e:
            logger.error(f"Fel vid kontroll av API-nycklar: {e}")
            return False
    
    def activate_production_mode(self):
        """Aktivera production mode"""
        try:
            # Uppdatera DEMO_MODE till false
            env_content = self.env_path.read_text()
            lines = env_content.split('\n')
            updated_lines = []
            
            demo_mode_found = False
            
            for line in lines:
                if line.startswith('DEMO_MODE='):
                    updated_lines.append('DEMO_MODE=false')
                    demo_mode_found = True
                else:
                    updated_lines.append(line)
            
            if not demo_mode_found:
                updated_lines.append('DEMO_MODE=false')
            
            self.env_path.write_text('\n'.join(updated_lines))
            
            logger.info("✅ Production mode aktiverat!")
            logger.info("🔄 Starta om servern för att använda riktiga API-anrop")
            
            # Skapa notification fil
            notification_file = Path('api_keys_updated.flag')
            notification_file.write_text(f"API keys updated at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Fel vid aktivering av production mode: {e}")

def create_api_key_instructions():
    """Skapa instruktionsfil för API-nycklar"""
    
    instructions = """
# 🔑 API-NYCKEL INSTRUKTIONER

## Hämta dina PressReader API-nycklar:

1. 🌐 Gå till: https://developers.pressreader.com/signin
2. 🔐 Logga in med: isak@allgot.se / Wdef3579!
3. 🔍 Leta efter "Applications", "API Keys", eller "Credentials"
4. ➕ Skapa nytt projekt om inget finns:
   - Namn: "Swedish News Userscript"
   - Beskrivning: "Userscript for Swedish news access"
5. 📋 Kopiera:
   - Client ID / API Key
   - Client Secret / API Secret

## Uppdatera .env filen:

Ersätt dessa rader i .env:
```
PRESSREADER_API_KEY=demo_key_replace_with_real
PRESSREADER_API_SECRET=demo_secret_replace_with_real
```

Med dina riktiga nycklar:
```
PRESSREADER_API_KEY=din_riktiga_client_id
PRESSREADER_API_SECRET=din_riktiga_client_secret
```

## Automatisk aktivering:

När du sparar .env med riktiga nycklar:
✅ Systemet upptäcker automatiskt förändringen
✅ Production mode aktiveras automatiskt
✅ Demo mode stängs av automatiskt

## Starta om servern:

```bash
# Stoppa nuvarande server (Ctrl+C)
# Starta igen:
python complete_server.py
```

Nu använder systemet riktiga PressReader API-anrop! 🚀
"""
    
    instructions_file = Path('API_KEYS_INSTRUCTIONS.md')
    instructions_file.write_text(instructions)
    
    print("📋 Instruktioner skapade: API_KEYS_INSTRUCTIONS.md")

def main():
    """Starta API-nyckel övervakaren"""
    
    # Skapa instruktioner
    create_api_key_instructions()
    
    # Kontrollera nuvarande status
    watcher = APIKeyWatcher()
    
    if watcher.check_api_keys():
        print("✅ Riktiga API-nycklar redan konfigurerade!")
        watcher.activate_production_mode()
    else:
        print("📋 Demo-nycklar aktiva - väntar på riktiga nycklar...")
        print("📖 Läs instruktioner i: API_KEYS_INSTRUCTIONS.md")
    
    # Starta filövervakare
    observer = Observer()
    observer.schedule(watcher, path='.', recursive=False)
    observer.start()
    
    print("👀 Övervakar .env fil för API-nyckel uppdateringar...")
    print("💡 Spara .env med riktiga nycklar för automatisk aktivering")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 API-nyckel övervakare stoppad")
    
    observer.join()

if __name__ == "__main__":
    # Installera watchdog om det saknas
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("📦 Installerar watchdog...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'watchdog'])
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    
    main()