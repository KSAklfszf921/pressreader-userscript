# PressReader API Setup Guide

## Steg 1: Hämta API-nycklar

1. **Logga in på PressReader Developer Portal:**
   - Gå till: https://developers.pressreader.com
   - Användarnamn: `isak@allgot.se`
   - Lösenord: `Wdef3579!`

2. **Skapa nytt API-projekt:**
   - Klicka på "Create New Application" eller "New Project"
   - Namn: "Swedish News Userscript"
   - Beskrivning: "Userscript for accessing Swedish newspapers via PressReader"
   - Välj "Discovery API" och "User Catalog API"

3. **Kopiera API-nycklar:**
   - API Key (Client ID)
   - API Secret (Client Secret)
   - Endpoint URLs

## Steg 2: Konfigurera miljövariabler

Skapa filen `.env` i `/Users/isakskogstad/Desktop/Isaks appar/PressReader_Extension_Latest/`:

```bash
# PressReader API Configuration
PRESSREADER_API_KEY=din_api_key_här
PRESSREADER_API_SECRET=din_api_secret_här
PRESSREADER_BASE_URL=https://api.prod.pressreader.com
PRESSREADER_DISCOVERY_URL=https://discovery.pressreader.com
```

## Steg 3: Installera dependencies

```bash
cd "/Users/isakskogstad/Desktop/Isaks appar/PressReader_Extension_Latest"
pip install python-dotenv requests fastapi uvicorn
```

## Steg 4: Kör setup-scriptet

```bash
python setup_api.py
```

## Steg 5: Starta servern

```bash
python pressreader_enhanced_server.py
```

## Testning

1. Gå till en SVD-artikel med paywall
2. Vänta 3 sekunder
3. Grön knapp ska visas
4. Klicka knappen → artikel hämtas från PressReader

## Felsökning

- Kolla console-loggar i webbläsaren
- Kontrollera server-loggar i terminal
- Verifiera API-nycklar är korrekta