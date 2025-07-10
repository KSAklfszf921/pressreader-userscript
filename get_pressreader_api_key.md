# Hur du får PressReader API-nyckel

## 🔑 Steg för att få API-nyckel:

### 1. **Registrera dig på PressReader Developer Portal**
- Gå till: https://developers.pressreader.com/
- Klicka på "Sign up"
- Skapa ett konto

### 2. **Kontakta PressReader**
- **Email**: api@pressreader.com
- **Ämne**: "API Access Request"
- **Meddelande exempel**:
```
Hej,

Jag skulle vilja ansöka om åtkomst till PressReader Discovery API för att utveckla ett verktyg som hjälper användare att hitta artiklar som är tillgängliga via PressReader.

Användningsfall:
- Detektera låsta artiklar på nyhetssajter
- Söka efter samma artiklar i PressReader
- Hjälpa användare att få laglig åtkomst till innehåll

Teknisk information:
- Förväntat antal API-anrop: ~1000/dag
- Språk: Python
- Målgrupp: Privatpersoner och bibliotek

Tack för er tid!

Med vänliga hälsningar,
[Ditt namn]
```

### 3. **Alternativ: Testa med Demo API-nyckel**
Vissa endpoints kan ha demo-åtkomst. Prova:
- Besök https://developers.pressreader.com/apis
- Logga in och kolla om det finns test-nycklar

## 🚀 **När du har API-nyckel:**

```bash
# Sätt API-nyckel
export PRESSREADER_API_KEY='din_api_nyckel_här'

# Testa samma artikel igen
python pressreader_enhanced.py --check-url "https://www.svd.se/a/63OwKL/har-kan-du-fa-mest-semester-for-pengarna"
```

## 🎯 **Förväntade resultat med API-nyckel:**

```json
{
  "url": "https://www.svd.se/a/63OwKL/har-kan-du-fa-mest-semester-for-pengarna",
  "is_locked": true,
  "lock_indicators_found": ["paywall", "subscribe", "prenumerera"],
  "pressreader_available": true,
  "pressreader_match": {
    "article": {
      "id": "12345",
      "title": "Här kan du få mest semester för pengarna",
      "author": "Författare",
      "url": "https://www.pressreader.com/sweden/svenska-dagbladet/..."
    },
    "match_score": 0.95
  },
  "check_timestamp": "2025-07-10T00:20:54.268100",
  "response_time_ms": 646
}
```

## 📞 **Kontaktinformation:**
- **PressReader API Support**: api@pressreader.com
- **Developer Portal**: https://developers.pressreader.com/
- **Care Center**: https://care.pressreader.com/