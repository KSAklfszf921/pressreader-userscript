# 🐙 GitHub Setup Guide

Allt är förberett! Du behöver bara köra dessa kommandon:

## 🚀 Snabb GitHub Setup (2 minuter)

### 1. Skapa GitHub Repository
```bash
# Gå till rätt mapp
cd "/Users/isakskogstad/Desktop/Isaks appar/PressReader_Extension_Latest"

# Skapa repo på GitHub (välj ett namn)
gh repo create pressreader-userscript --public --description "Advanced PressReader UserScript for Swedish News"

# Lägg till remote
git remote add origin https://github.com/isakskogstad/pressreader-userscript.git
```

### 2. Pusha allt till GitHub
```bash
# Pusha till GitHub
git push -u origin master
```

### 3. Lägg till API-nycklar som GitHub Secrets
```bash
# När du har PressReader API-nycklar:
gh secret set PRESSREADER_API_KEY
gh secret set PRESSREADER_API_SECRET
```

## 🔄 Alternativ: Använda GitHub Web Interface

1. **Gå till GitHub.com**
2. **Klicka "New Repository"**
3. **Namn:** `pressreader-userscript`
4. **Beskrivning:** "Advanced PressReader UserScript for Swedish News"
5. **Public repository**
6. **Skapa repository**

7. **Kopiera repository URL och kör:**
```bash
cd "/Users/isakskogstad/Desktop/Isaks appar/PressReader_Extension_Latest"
git remote add origin https://github.com/isakskogstad/pressreader-userscript.git
git push -u origin master
```

## ⚡ GitHub Codespaces (Cloud Development)

Efter att du pushat till GitHub:

1. **Gå till ditt repo på GitHub**
2. **Klicka "Code" → "Codespaces" → "Create codespace"**
3. **Lägg till API-nycklar som environment secrets**
4. **Allt körs automatiskt i molnet!**

## 🤖 GitHub Actions (Automatisk Deploy)

GitHub Actions är redan konfigurerat! När du pushar kod:
- ✅ Automatisk testing
- ✅ Bygg userscript bundle
- ✅ Deploy till cloud (om konfigurerat)

## 🔐 API Keys Management

### Via GitHub CLI:
```bash
gh secret set PRESSREADER_API_KEY --body "din_api_nyckel"
gh secret set PRESSREADER_API_SECRET --body "din_api_secret"
```

### Via GitHub Web:
1. Gå till ditt repo
2. Settings → Secrets and variables → Actions
3. Klicka "New repository secret"
4. Lägg till `PRESSREADER_API_KEY` och `PRESSREADER_API_SECRET`

## 🎯 Efter GitHub Setup

Din repository kommer ha:
- ✅ Komplett userscript system
- ✅ Automatisk CI/CD
- ✅ Cloud development environment
- ✅ Demo mode för omedelbar testning
- ✅ Produktionsklart för PressReader API

## 📋 Repository Features

Efter push får du:
- 📚 **Snygg README** med all dokumentation
- 🔧 **GitHub Actions** för automatisk deploy
- 🌐 **Codespaces** för cloud development
- 🐳 **DevContainer** konfiguration
- 📦 **Requirements.txt** för dependencies
- 🔒 **Gitignore** för säkerhet

---

**Allt är förberett - bara pusha till GitHub! 🚀**