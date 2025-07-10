#!/usr/bin/env python3
"""
Enhanced Demo Server med realistiska PressReader URLs
Bygger vidare på complete_server.py men med bättre mock-data
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import hashlib
import time
import json
import random
import re
from datetime import datetime, timedelta

app = FastAPI(
    title="PressReader API Server - Enhanced Demo",
    version="2.1.0",
    description="Enhanced demo mode with realistic PressReader URLs and content"
)

# Enhanced mock database with realistic PressReader URLs
ENHANCED_MOCK_DATABASE = {
    "svd": {
        "publication_id": "283839766543162",
        "publication_name": "Svenska Dagbladet",
        "country": "sweden",
        "base_url": "https://www.pressreader.com/sweden/svenska-dagbladet",
        "articles": [
            {
                "title_keywords": ["bingo", "adhd", "form", "50"],
                "article": {
                    "title": "Bingo rimer mot sitt livs form vid 50 - min ADHD som turbo",
                    "author": "Maria Lindström",
                    "date": "2025-01-10",
                    "section": "Kultur",
                    "url": "https://www.pressreader.com/sweden/svenska-dagbladet/20250110/283839766543162",
                    "full_content": "Bingo Rimér berättar om hur hans ADHD-diagnos vid 50 års ålder förändrade hans liv och kreativitet. 'Det var som att få en turbo på hjärnan', säger han i denna djupgående intervju om musik, kreativitet och att hitta sin plats i livet.",
                    "image_url": "https://www.pressreader.com/sweden/svenska-dagbladet/20250110/283839766543162/image.jpg"
                }
            },
            {
                "title_keywords": ["politik", "sverige", "eu"],
                "article": {
                    "title": "Sveriges EU-strategi under förhandling",
                    "author": "Anders Carlsson",
                    "date": "2025-01-10", 
                    "section": "Politik",
                    "url": "https://www.pressreader.com/sweden/svenska-dagbladet/20250110/283839766543163",
                    "full_content": "Regeringen presenterar ny strategi för Sveriges roll i EU. Fokus ligger på klimat och säkerhet enligt källor inom Rosenbad."
                }
            }
        ]
    },
    "kungalvsposten": {
        "publication_id": "283839766543164",
        "publication_name": "Kungälvs-Posten",
        "country": "sweden",
        "base_url": "https://www.pressreader.com/sweden/kungalvs-posten",
        "articles": [
            {
                "title_keywords": ["pop", "city", "container", "grillkorv"],
                "article": {
                    "title": "Pop up city bjöd på containerhäng och grillkorv",
                    "author": "Lena Andersson",
                    "date": "2025-01-10",
                    "section": "Lokala nyheter",
                    "url": "https://www.pressreader.com/sweden/kungalvs-posten/20250110/283839766543164",
                    "full_content": "Kungälvs nya pop-up område lockade hundratals besökare under helgen. Containrar förvandlades till små butiker och restauranger, medan grillkorv serverades från foodtrucks. 'Det är fantastiskt att se hur kreativa våra lokala företagare är', säger kommunalrådet.",
                    "image_url": "https://www.pressreader.com/sweden/kungalvs-posten/20250110/283839766543164/image.jpg"
                }
            },
            {
                "title_keywords": ["skola", "elever", "kungälv"],
                "article": {
                    "title": "Nya skolan öppnar till hösten",
                    "author": "Per Johansson",
                    "date": "2025-01-10",
                    "section": "Utbildning",
                    "url": "https://www.pressreader.com/sweden/kungalvs-posten/20250110/283839766543165",
                    "full_content": "Kungälvs kommun satsar stort på utbildning med en helt ny skola som öppnar till hösten. Skolan kommer att rymma 500 elever och ha moderna klassrum."
                }
            }
        ]
    }
}

class ArticleRequest(BaseModel):
    url: str
    title: Optional[str] = None
    site: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None

class SessionRequest(BaseModel):
    user_agent: Optional[str] = None

def generate_realistic_pressreader_url(site: str, title: str) -> str:
    """Generera realistisk PressReader URL baserat på site och titel"""
    
    # Hämta publication data
    pub_data = ENHANCED_MOCK_DATABASE.get(site, {})
    if not pub_data:
        # Fallback för okända sites
        pub_id = str(hash(site) % 999999999999999)
        return f"https://www.pressreader.com/sweden/unknown-publication/{datetime.now().strftime('%Y%m%d')}/{pub_id}"
    
    # Använd dagens datum
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Generera artikel-ID baserat på titel
    article_id = abs(hash(title)) % 999999999999999
    
    return f"{pub_data['base_url']}/{date_str}/{article_id}"

def find_best_matching_article(site: str, title: str, url: str) -> Dict[str, Any]:
    """Hitta bästa matchande artikel baserat på titel och keywords"""
    
    if not title:
        title = extract_title_from_url(url)
    
    site_data = ENHANCED_MOCK_DATABASE.get(site, {})
    if not site_data:
        return generate_generic_article(site, title, url)
    
    # Normalisera titel för sökning
    title_lower = title.lower()
    title_words = re.findall(r'\w+', title_lower)
    
    best_match = None
    best_score = 0
    
    for article_data in site_data.get("articles", []):
        keywords = article_data.get("title_keywords", [])
        
        # Beräkna match score
        score = 0
        for keyword in keywords:
            if keyword.lower() in title_lower:
                score += 1
        
        # Normalisera score
        if keywords:
            score = score / len(keywords)
        
        if score > best_score:
            best_score = score
            best_match = article_data
    
    if best_match and best_score > 0.3:
        article = best_match["article"].copy()
        # Uppdatera URL om det inte är exakt match
        if best_score < 0.8:
            article["url"] = generate_realistic_pressreader_url(site, title)
            article["title"] = title
        return {
            "article": article,
            "match_score": min(0.95, 0.7 + best_score * 0.2),
            "strategy": "Enhanced Keyword Match"
        }
    
    return generate_generic_article(site, title, url)

def generate_generic_article(site: str, title: str, url: str) -> Dict[str, Any]:
    """Generera generisk artikel för okänd content"""
    
    site_data = ENHANCED_MOCK_DATABASE.get(site, {})
    pub_name = site_data.get("publication_name", site.title())
    
    return {
        "article": {
            "title": title or "Artikel från " + pub_name,
            "author": "Redaktionen",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "section": "Nyheter",
            "url": generate_realistic_pressreader_url(site, title or "artikel"),
            "full_content": f"Detta är en artikel från {pub_name}. I production mode skulle detta vara riktigt innehåll från PressReader API.",
            "copyright": f"© {pub_name} {datetime.now().year}"
        },
        "match_score": 0.75,
        "strategy": "Enhanced Generic Match"
    }

def extract_title_from_url(url: str) -> str:
    """Extrahera titel från URL"""
    # Försök extrahera från URL slug
    parts = url.split('/')
    if len(parts) > 0:
        slug = parts[-1]
        # Konvertera slug till läsbar titel
        title = slug.replace('-', ' ').replace('_', ' ')
        return title.title()
    return "Untitled Article"

@app.get("/")
async def root():
    return {
        "service": "PressReader API Server - Enhanced Demo",
        "version": "2.1.0",
        "status": "online",
        "mode": "enhanced_demo",
        "features": ["realistic_urls", "keyword_matching", "content_generation"],
        "endpoints": ["/api/v2/sessions", "/api/v2/check-article"]
    }

@app.post("/api/v2/sessions")
async def create_session(request: SessionRequest):
    """Skapa ny session"""
    session_id = f"session_{int(time.time())}_{random.randint(0, 9999)}"
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Session skapad framgångsrikt",
        "mode": "enhanced_demo"
    }

@app.post("/api/v2/check-article")
async def check_article(request: ArticleRequest):
    """Kontrollera artikel i PressReader med enhanced demo data"""
    
    # Extrahera site från URL
    site = request.site
    if not site:
        if 'svd.se' in request.url:
            site = 'svd'
        elif 'kungalvsposten.se' in request.url:
            site = 'kungalvsposten'
        else:
            site = 'unknown'
    
    # Hitta bästa matchande artikel
    match_data = find_best_matching_article(site, request.title, request.url)
    
    # Lägg till search result metadata
    site_data = ENHANCED_MOCK_DATABASE.get(site, {})
    search_result = {
        "publication": {
            "title": site_data.get("publication_name", site.title()),
            "country": site_data.get("country", "sweden"),
            "id": site_data.get("publication_id", "unknown")
        },
        "issue": {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "pages": random.randint(20, 80)
        },
        "search_query": request.title or "article search",
        "total_results": random.randint(1, 5)
    }
    
    return {
        "success": True,
        "result": {
            "pressreader_available": True,
            "pressreader_match": {
                "article": match_data["article"],
                "search_result": search_result,
                "match_score": match_data["match_score"],
                "strategy_used": match_data["strategy"]
            }
        },
        "message": "ENHANCED DEMO: Artikel hittad med realistisk PressReader URL",
        "note": "Detta är enhanced demo mode med realistiska URLs och content"
    }

if __name__ == "__main__":
    print("🚀 Enhanced PressReader Demo Server")
    print("==================================")
    print("✨ Features:")
    print("   - Realistiska PressReader URLs")
    print("   - Intelligent keyword matching")
    print("   - Enhanced content generation")
    print("   - Accurate publication metadata")
    print()
    print("🌐 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)