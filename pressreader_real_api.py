#!/usr/bin/env python3
"""
Real PressReader API Integration
Ersätter mock-data med riktiga PressReader API-anrop
"""

import os
import sys
import json
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Läs miljövariabler
from dotenv import load_dotenv
load_dotenv()

# Konfigurera logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PressReaderConfig:
    """PressReader API konfiguration"""
    api_key: str
    api_secret: str
    base_url: str
    discovery_url: str
    timeout: int = 30
    max_retries: int = 3

class RealPressReaderClient:
    """Riktig PressReader API-klient"""
    
    def __init__(self, config: PressReaderConfig):
        self.config = config
        self.session = requests.Session()
        self.auth_token = None
        self.token_expires = None
        
        # Konfigurera session headers
        self.session.headers.update({
            'User-Agent': 'Swedish-News-Userscript/2.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    async def authenticate(self) -> bool:
        """Autentisera med PressReader API"""
        try:
            auth_url = f"{self.config.base_url}/auth/token"
            
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.config.api_key,
                'client_secret': self.config.api_secret
            }
            
            logger.info(f"Autentiserar med PressReader API: {auth_url}")
            
            response = self.session.post(
                auth_url,
                json=auth_data,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get('access_token')
                
                # Beräkna när token upphör att gälla
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min marginal
                
                # Uppdatera session headers
                self.session.headers['Authorization'] = f"Bearer {self.auth_token}"
                
                logger.info("✅ PressReader autentisering lyckades")
                return True
            else:
                logger.error(f"❌ Autentisering misslyckades: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Autentiseringsfel: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """Kontrollera om auth token fortfarande är giltig"""
        if not self.auth_token or not self.token_expires:
            return False
        return datetime.now() < self.token_expires
    
    async def ensure_authenticated(self) -> bool:
        """Säkerställ att vi är autentiserade"""
        if not self.is_token_valid():
            return await self.authenticate()
        return True
    
    async def search_articles(self, 
                            query: str,
                            publication: Optional[str] = None,
                            author: Optional[str] = None,
                            date_from: Optional[str] = None,
                            date_to: Optional[str] = None,
                            limit: int = 20) -> Dict[str, Any]:
        """Sök artiklar i PressReader"""
        
        if not await self.ensure_authenticated():
            return {"success": False, "error": "Autentisering misslyckades"}
        
        try:
            search_url = f"{self.config.discovery_url}/search"
            
            # Konstruera sökparametrar
            search_params = {
                'query': query,
                'limit': limit,
                'offset': 0
            }
            
            # Lägg till filter om de finns
            filters = []
            
            if publication:
                filters.append(f"publication:'{publication}'")
            
            if author:
                filters.append(f"author:'{author}'")
            
            if date_from:
                filters.append(f"date:['{date_from}' TO *]")
            elif date_to:
                filters.append(f"date:[* TO '{date_to}']")
            
            if filters:
                search_params['filter'] = ' AND '.join(filters)
            
            logger.info(f"🔍 Söker artiklar: {query}")
            logger.debug(f"Sökparametrar: {search_params}")
            
            response = self.session.get(
                search_url,
                params=search_params,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                results = response.json()
                logger.info(f"✅ Hittade {len(results.get('articles', []))} artiklar")
                return {
                    "success": True,
                    "results": results,
                    "query": query,
                    "total_found": len(results.get('articles', []))
                }
            else:
                logger.error(f"❌ Sökfel: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API-fel: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Sökfel: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_article_details(self, article_id: str) -> Dict[str, Any]:
        """Hämta detaljerad artikelinformation"""
        
        if not await self.ensure_authenticated():
            return {"success": False, "error": "Autentisering misslyckades"}
        
        try:
            article_url = f"{self.config.base_url}/articles/{article_id}"
            
            logger.info(f"📰 Hämtar artikel: {article_id}")
            
            response = self.session.get(
                article_url,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                article_data = response.json()
                logger.info("✅ Artikel hämtad")
                return {
                    "success": True,
                    "article": article_data
                }
            else:
                logger.error(f"❌ Fel vid artikelhämtning: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Artikel inte tillgänglig: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"❌ Artikelhämtningsfel: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def find_article_by_strategies(self, strategies: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        """Sök artikel med flera strategier"""
        
        for i, strategy in enumerate(strategies, 1):
            logger.info(f"🎯 Strategi {i}/{len(strategies)}: {strategy['name']}")
            
            # Extrahera sökparametrar från strategin
            search_data = strategy.get('searchData', {})
            query = search_data.get('search_query', search_data.get('title', ''))
            publication = search_data.get('publication')
            author = search_data.get('author')
            
            if not query and 'url' in search_data:
                # URL-baserad sökning - försök extrahera titel från URL
                url = search_data['url']
                query = self.extract_title_from_url(url)
            
            if not query:
                logger.warning(f"⚠️  Ingen sökfråga för strategi: {strategy['name']}")
                continue
            
            # Utför sökning
            result = await self.search_articles(
                query=query,
                publication=publication,
                author=author,
                limit=10
            )
            
            if result['success'] and result.get('total_found', 0) > 0:
                articles = result['results'].get('articles', [])
                if articles:
                    best_match = articles[0]  # Ta första träffen
                    
                    # Beräkna matchpoäng (förenklat)
                    match_score = self.calculate_match_score(search_data, best_match)
                    
                    logger.info(f"✅ Artikel hittad med strategi '{strategy['name']}' (score: {match_score:.2f})")
                    
                    return True, {
                        "pressreader_available": True,
                        "pressreader_match": {
                            "article": best_match,
                            "search_result": result['results'],
                            "match_score": match_score,
                            "strategy_used": strategy['name']
                        }
                    }
            
            # Kort paus mellan strategier
            await asyncio.sleep(0.5)
        
        logger.info("❌ Ingen artikel hittad med någon strategi")
        return False, {"pressreader_available": False}
    
    def extract_title_from_url(self, url: str) -> str:
        """Försök extrahera titel från URL"""
        try:
            # För svenska nyhetsartiklar, titel ofta i URL efter sista /
            parts = url.split('/')
            if len(parts) > 1:
                last_part = parts[-1]
                # Ta bort UUID och filändelser
                title_part = last_part.split('.')[0]
                # Ersätt bindestreck med mellanslag
                title = title_part.replace('-', ' ').replace('_', ' ')
                return title
        except:
            pass
        
        return ""
    
    def calculate_match_score(self, search_data: Dict[str, Any], article: Dict[str, Any]) -> float:
        """Beräkna hur väl artikel matchar sökdata"""
        score = 0.0
        factors = 0
        
        # Jämför titel
        search_title = search_data.get('title', '').lower()
        article_title = article.get('title', '').lower()
        
        if search_title and article_title:
            # Enkel Levenshtein-liknande jämförelse
            title_similarity = len(set(search_title.split()) & set(article_title.split())) / max(len(search_title.split()), len(article_title.split()))
            score += title_similarity * 0.6
            factors += 1
        
        # Jämför författare
        search_author = search_data.get('author', '').lower()
        article_author = article.get('author', '').lower()
        
        if search_author and article_author:
            if search_author in article_author or article_author in search_author:
                score += 0.3
            factors += 1
        
        # Jämför publikation
        search_pub = search_data.get('publication', '').lower()
        article_pub = article.get('publication', {}).get('title', '').lower()
        
        if search_pub and article_pub:
            if search_pub in article_pub or article_pub in search_pub:
                score += 0.1
            factors += 1
        
        return score / max(factors, 1) if factors > 0 else 0.0

def create_pressreader_client() -> Optional[RealPressReaderClient]:
    """Skapa PressReader-klient från miljövariabler"""
    
    api_key = os.getenv('PRESSREADER_API_KEY')
    api_secret = os.getenv('PRESSREADER_API_SECRET')
    base_url = os.getenv('PRESSREADER_BASE_URL', 'https://api.prod.pressreader.com')
    discovery_url = os.getenv('PRESSREADER_DISCOVERY_URL', 'https://discovery.pressreader.com')
    
    if not api_key or not api_secret:
        logger.error("❌ PRESSREADER_API_KEY och PRESSREADER_API_SECRET måste konfigureras i .env")
        return None
    
    if api_key == 'your_api_key_here' or api_secret == 'your_api_secret_here':
        logger.error("❌ API-nycklar behöver uppdateras i .env filen")
        return None
    
    config = PressReaderConfig(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url,
        discovery_url=discovery_url
    )
    
    return RealPressReaderClient(config)

# Test-funktion
async def test_api():
    """Testa API-anslutning"""
    client = create_pressreader_client()
    if not client:
        return False
    
    print("🧪 Testar PressReader API...")
    
    # Test autentisering
    if await client.authenticate():
        print("✅ Autentisering lyckades")
        
        # Test-sökning
        result = await client.search_articles("Sverige", limit=5)
        if result['success']:
            print(f"✅ Testsökning lyckades: {result['total_found']} artiklar hittade")
            return True
        else:
            print(f"❌ Testsökning misslyckades: {result.get('error')}")
    else:
        print("❌ Autentisering misslyckades")
    
    return False

if __name__ == "__main__":
    # Kör test
    asyncio.run(test_api())