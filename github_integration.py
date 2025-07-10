#!/usr/bin/env python3
"""
GitHub Integration för PressReader API
Använder GitHub Secrets eller Actions för att hantera API-nycklar säkert
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from cryptography.fernet import Fernet

def check_github_cli():
    """Kontrollera om GitHub CLI är installerat"""
    try:
        import subprocess
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub CLI installerat")
            return True
    except:
        pass
    
    print("❌ GitHub CLI saknas")
    print("💡 Installera med: brew install gh")
    return False

def github_auth_status():
    """Kontrollera GitHub autentiseringsstatus"""
    try:
        import subprocess
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if "Logged in" in result.stderr:
            print("✅ Inloggad på GitHub")
            return True
        else:
            print("❌ Inte inloggad på GitHub")
            print("💡 Logga in med: gh auth login")
            return False
    except Exception as e:
        print(f"❌ GitHub auth-fel: {e}")
        return False

def create_github_repo_secrets():
    """Skapa GitHub repository secrets för API-nycklar"""
    try:
        import subprocess
        
        # Läs från .env om den finns
        env_path = Path('.env')
        if not env_path.exists():
            print("❌ .env fil saknas")
            return False
        
        env_content = env_path.read_text()
        api_key = None
        api_secret = None
        
        for line in env_content.split('\n'):
            if line.startswith('PRESSREADER_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
            elif line.startswith('PRESSREADER_API_SECRET='):
                api_secret = line.split('=', 1)[1].strip()
        
        if not api_key or not api_secret or api_key == 'your_api_key_here':
            print("❌ API-nycklar inte konfigurerade i .env")
            return False
        
        print("🔐 Skapar GitHub repository secrets...")
        
        # Sätt secrets via GitHub CLI
        commands = [
            ['gh', 'secret', 'set', 'PRESSREADER_API_KEY', '--body', api_key],
            ['gh', 'secret', 'set', 'PRESSREADER_API_SECRET', '--body', api_secret]
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Secret {cmd[3]} skapad")
            else:
                print(f"❌ Fel vid skapande av {cmd[3]}: {result.stderr}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub secrets-fel: {e}")
        return False

def create_github_action():
    """Skapa GitHub Action för automatisk deploy"""
    
    action_content = """name: PressReader API Deploy

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

env:
  PRESSREADER_API_KEY: ${{ secrets.PRESSREADER_API_KEY }}
  PRESSREADER_API_SECRET: ${{ secrets.PRESSREADER_API_SECRET }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install python-dotenv requests fastapi uvicorn
    
    - name: Create .env file
      run: |
        echo "PRESSREADER_API_KEY=${{ secrets.PRESSREADER_API_KEY }}" > .env
        echo "PRESSREADER_API_SECRET=${{ secrets.PRESSREADER_API_SECRET }}" >> .env
        echo "PRESSREADER_BASE_URL=https://api.prod.pressreader.com" >> .env
        echo "PRESSREADER_DISCOVERY_URL=https://discovery.pressreader.com" >> .env
    
    - name: Test API connection
      run: |
        python pressreader_real_api.py
    
    - name: Build userscript bundle
      run: |
        echo "// PressReader UserScript - Built $(date)" > pressreader_userscript_built.js
        cat pressreader_userscript.js >> pressreader_userscript_built.js
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: pressreader-userscript
        path: |
          pressreader_userscript_built.js
          pressreader_real_api.py
          api_config.json

  # Optional: Deploy to cloud service
  # deploy-to-cloud:
  #   needs: deploy
  #   runs-on: ubuntu-latest
  #   steps:
  #   - name: Deploy to Railway/Render/etc
  #     run: echo "Deploy to your preferred cloud service"
"""
    
    # Skapa .github/workflows mapp
    github_dir = Path('.github')
    workflows_dir = github_dir / 'workflows'
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    # Skriv action-fil
    action_file = workflows_dir / 'pressreader-deploy.yml'
    action_file.write_text(action_content)
    
    print("✅ GitHub Action skapad: .github/workflows/pressreader-deploy.yml")
    return True

def setup_github_codespaces():
    """Konfigurera för GitHub Codespaces"""
    
    devcontainer_content = {
        "name": "PressReader Development",
        "image": "mcr.microsoft.com/devcontainers/python:3.10",
        "features": {
            "ghcr.io/devcontainers/features/github-cli:1": {}
        },
        "postCreateCommand": "pip install -r requirements.txt",
        "forwardPorts": [8000],
        "customizations": {
            "vscode": {
                "extensions": [
                    "ms-python.python",
                    "ms-python.pylint",
                    "usernamehw.errorlens"
                ]
            }
        },
        "secrets": {
            "PRESSREADER_API_KEY": {
                "description": "PressReader API Key"
            },
            "PRESSREADER_API_SECRET": {
                "description": "PressReader API Secret"
            }
        }
    }
    
    # Skapa .devcontainer mapp
    devcontainer_dir = Path('.devcontainer')
    devcontainer_dir.mkdir(exist_ok=True)
    
    # Skriv devcontainer.json
    devcontainer_file = devcontainer_dir / 'devcontainer.json'
    devcontainer_file.write_text(json.dumps(devcontainer_content, indent=2))
    
    print("✅ GitHub Codespaces konfiguration skapad")
    return True

def create_requirements_txt():
    """Skapa requirements.txt för GitHub integration"""
    
    requirements = """python-dotenv>=1.0.0
requests>=2.28.0
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
pydantic>=2.0.0
cryptography>=41.0.0
selenium>=4.15.0
"""
    
    req_file = Path('requirements.txt')
    req_file.write_text(requirements)
    
    print("✅ requirements.txt skapad")
    return True

def github_integration_guide():
    """Visa guide för GitHub integration"""
    
    print("\n" + "="*60)
    print("🚀 GITHUB INTEGRATION GUIDE")
    print("="*60)
    print("\n📋 STEG FÖR GITHUB SETUP:")
    
    print("\n1. 🔧 Installera GitHub CLI:")
    print("   brew install gh")
    
    print("\n2. 🔐 Logga in på GitHub:")
    print("   gh auth login")
    
    print("\n3. 📁 Skapa GitHub repository:")
    print("   gh repo create pressreader-userscript --public")
    print("   git remote add origin https://github.com/ditt-användarnamn/pressreader-userscript.git")
    
    print("\n4. 🔑 Lägg till API-nycklar som secrets:")
    print("   gh secret set PRESSREADER_API_KEY")
    print("   gh secret set PRESSREADER_API_SECRET")
    
    print("\n5. 🚀 Push kod till GitHub:")
    print("   git add .")
    print("   git commit -m 'Initial PressReader userscript'")
    print("   git push -u origin main")
    
    print("\n6. ⚡ GitHub Actions kör automatiskt!")
    
    print("\n💡 ALTERNATIV - GitHub Codespaces:")
    print("   - Öppna ditt repo på github.com")
    print("   - Klicka 'Code' > 'Codespaces' > 'Create codespace'")
    print("   - Ange API-nycklar som environment secrets")
    
    print("\n" + "="*60)

def main():
    """Huvudfunktion för GitHub integration"""
    print("🐙 PressReader GitHub Integration Setup")
    print("="*50)
    
    # Skapa nödvändiga filer
    create_requirements_txt()
    create_github_action()
    setup_github_codespaces()
    
    # Kontrollera GitHub CLI
    if check_github_cli():
        if github_auth_status():
            # Försök skapa secrets
            if create_github_repo_secrets():
                print("\n✅ GitHub integration klar!")
                print("🚀 Push till GitHub för att aktivera Actions")
            else:
                print("\n⚠️  Manuell secret-konfiguration krävs")
        else:
            print("\n⚠️  GitHub-inloggning krävs")
    
    # Visa guide oavsett
    github_integration_guide()

if __name__ == "__main__":
    main()