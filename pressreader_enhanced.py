#!/usr/bin/env python3
"""
Enhanced PressReader Article Access System
==========================================

Uppdaterad och perfekt version baserad på verklig OpenAPI-specifikation.
Säkerställer flexibilitet, användarlogging och omedelbar identifiering av låsta artiklar.

Funktioner:
- Korrekt API-implementation baserad på OpenAPI spec
- POST-request för /discovery/v1/search med JSON body
- Användarsessioner och aktivitetslogging
- Omedelbar låst artikel-detektering och PressReader-lookup
- Flexibel konfiguration och cachning
- Avancerad matchningsalgoritm
- Stöd för komplex query-syntax
"""

import requests
import json
import time
import logging
import hashlib
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs
import re
from dataclasses import dataclass, asdict
from threading import Lock
import concurrent.futures
import uuid

# Konfigurera logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pressreader_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UserSession:
    """Användarsession för att hålla koll på användarens aktivitet"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    total_checks: int = 0
    successful_matches: int = 0
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}

@dataclass
class ArticleMatch:
    """Struktur för artikel-matchning"""
    original_url: str
    pressreader_article: Dict[str, Any]
    match_score: float
    matched_at: datetime
    session_id: str

@dataclass
class SearchRequest:
    """Sökförfrågan enligt OpenAPI spec"""
    query: str
    countries: List[str]
    itemTypes: str = "article"
    author: Optional[str] = None
    cids: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    searchIn: str = "everywhere"
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class EnhancedPressReaderClient:
    """
    Förbättrad PressReader-klient baserad på verklig OpenAPI-specifikation
    """
    
    def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
        """
        Initialisera enhanced PressReader-klient
        
        Args:
            api_key: PressReader API-nyckel
            config: Konfigurationsinställningar
        """
        self.api_key = api_key or self._get_api_key()
        self.config = config or self._load_config()
        self.base_url = "https://api.pressreader.com"  # Korrekt från OpenAPI spec
        self.session = requests.Session()
        self.cache_db = "pressreader_cache.db"
        self.user_sessions: Dict[str, UserSession] = {}
        self.session_lock = Lock()
        
        # Sätt upp session headers
        if self.api_key:
            self.session.headers.update({
                'api-key': self.api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'PressReader-Enhanced-Client/2.0'
            })
        
        # Initialisera databas
        self._init_database()
        
        # Ladda låsta artikel-indikatorer
        self.lock_indicators = self._load_lock_indicators()
        
        logger.info("Enhanced PressReader Client initialiserad")
    
    def _get_api_key(self) -> Optional[str]:
        """Hämta API-nyckel från miljövariabler eller config"""
        import os
        
        # Miljövariabel
        api_key = os.getenv('PRESSREADER_API_KEY')
        if api_key:
            return api_key
        
        # Konfigurationsfil
        try:
            with open('pressreader_config.json', 'r') as f:
                config = json.load(f)
                return config.get('api_key')
        except FileNotFoundError:
            logger.warning("Ingen API-nyckel hittad")
            return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Ladda konfiguration"""
        default_config = {
            'max_search_results': 20,
            'search_timeout': 30,
            'cache_timeout': 3600,  # 1 timme
            'default_countries': ['SE', 'NO', 'DK', 'FI'],
            'default_languages': ['sv', 'en', 'no', 'da'],
            'match_threshold': 0.75,
            'concurrent_searches': 5,
            'rate_limit_per_hour': 1000,
            'user_session_timeout': 1800,  # 30 minuter
            'enable_logging': True,
            'enable_caching': True
        }
        
        try:
            with open('pressreader_enhanced_config.json', 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            logger.info("Använder standardkonfiguration")
        
        return default_config
    
    def _init_database(self):
        """Initialisera SQLite-databas för caching och logging"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Tabell för cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query_params TEXT,
                results TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        # Tabell för användarsessioner
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TIMESTAMP,
                last_activity TIMESTAMP,
                total_checks INTEGER,
                successful_matches INTEGER,
                preferences TEXT
            )
        ''')
        
        # Tabell för artikel-matchningar
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS article_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT,
                pressreader_article TEXT,
                match_score REAL,
                matched_at TIMESTAMP,
                session_id TEXT
            )
        ''')
        
        # Tabell för aktivitetslogging
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_lock_indicators(self) -> List[str]:
        """Ladda indikatorer för låsta artiklar"""
        return [
            # Engelska
            'paywall', 'subscribe', 'subscription', 'premium', 'member only',
            'requires subscription', 'sign up', 'register', 'login required',
            'locked content', 'restricted access', 'behind paywall',
            'subscriber exclusive', 'premium content', 'paid content',
            
            # Svenska
            'betalvägg', 'prenumerera', 'prenumeration', 'medlemskap',
            'kräver prenumeration', 'registrera', 'logga in', 'låst innehåll',
            'begränsad åtkomst', 'prenumerantexklusivt', 'betalt innehåll',
            
            # Norska
            'betalingsmur', 'abonner', 'abonnement', 'medlemskap',
            'krever abonnement', 'registrer', 'logg inn',
            
            # Danska
            'betalingsmur', 'abonner', 'abonnement', 'medlemskab',
            'kræver abonnement', 'registrer', 'log ind'
        ]
    
    def create_user_session(self, user_id: str = None) -> str:
        """Skapa ny användarsession"""
        session_id = str(uuid.uuid4())
        user_id = user_id or f"user_{int(time.time())}"
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        with self.session_lock:
            self.user_sessions[session_id] = session
        
        # Spara i databas
        self._save_user_session(session)
        self._log_activity(session_id, "session_created", {"user_id": user_id})
        
        logger.info(f"Ny användarsession skapad: {session_id}")
        return session_id
    
    def _save_user_session(self, session: UserSession):
        """Spara användarsession i databas"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_sessions 
            (session_id, user_id, created_at, last_activity, total_checks, 
             successful_matches, preferences)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.session_id,
            session.user_id,
            session.created_at,
            session.last_activity,
            session.total_checks,
            session.successful_matches,
            json.dumps(session.preferences)
        ))
        
        conn.commit()
        conn.close()
    
    def _log_activity(self, session_id: str, action: str, details: Dict[str, Any]):
        """Logga användaraktivitet"""
        if not self.config.get('enable_logging', True):
            return
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_log (session_id, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (session_id, action, json.dumps(details), datetime.now()))
        
        conn.commit()
        conn.close()
    
    def is_article_locked(self, article_url: str, session_id: str = None) -> Dict[str, Any]:
        """
        Förbättrad detektering av låsta artiklar med omedelbar kontroll
        
        Args:
            article_url: URL till artikel
            session_id: Användarsession-ID
            
        Returns:
            Dict med resultat och metadata
        """
        if session_id:
            self._update_session_activity(session_id)
            self._log_activity(session_id, "article_check_started", {"url": article_url})
        
        result = {
            'url': article_url,
            'is_locked': False,
            'lock_indicators_found': [],
            'pressreader_available': False,
            'check_timestamp': datetime.now().isoformat(),
            'response_time_ms': 0
        }
        
        start_time = time.time()
        
        try:
            # Hämta sidinnehåll
            response = requests.get(article_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            
            content = response.text.lower()
            
            # Kontrollera för låsta artikel-indikatorer
            found_indicators = []
            for indicator in self.lock_indicators:
                if indicator.lower() in content:
                    found_indicators.append(indicator)
            
            result['is_locked'] = len(found_indicators) > 0
            result['lock_indicators_found'] = found_indicators
            
            if result['is_locked']:
                logger.info(f"Låst artikel detekterad: {article_url}")
                
                # Omedelbar PressReader-lookup
                article_info = self._extract_article_info(response.text, article_url)
                pressreader_match = self._immediate_pressreader_lookup(article_info, session_id)
                
                if pressreader_match:
                    result['pressreader_available'] = True
                    result['pressreader_match'] = pressreader_match
                    
                    if session_id:
                        self._log_activity(session_id, "pressreader_match_found", {
                            "original_url": article_url,
                            "match_score": pressreader_match.get('match_score', 0)
                        })
        
        except requests.RequestException as e:
            logger.error(f"Fel vid kontroll av artikel: {e}")
            result['error'] = str(e)
        
        finally:
            result['response_time_ms'] = int((time.time() - start_time) * 1000)
            
            if session_id:
                self._update_session_activity(session_id)
                self._log_activity(session_id, "article_check_completed", result)
        
        return result
    
    def _extract_article_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extrahera artikelinformation från HTML"""
        info = {
            'title': '',
            'author': '',
            'publication_date': '',
            'description': '',
            'keywords': [],
            'url': url
        }
        
        # Extrahera titel
        title_patterns = [
            r'<title[^>]*>([^<]+)</title>',
            r'<h1[^>]*>([^<]+)</h1>',
            r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)',
            r'<meta[^>]*name=["\']title["\'][^>]*content=["\']([^"\']+)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                info['title'] = match.group(1).strip()
                break
        
        # Extrahera författare
        author_patterns = [
            r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)',
            r'<span[^>]*class=["\'][^"\']*author[^"\']*["\'][^>]*>([^<]+)',
            r'<div[^>]*class=["\'][^"\']*byline[^"\']*["\'][^>]*>([^<]+)',
            r'<meta[^>]*property=["\']article:author["\'][^>]*content=["\']([^"\']+)'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                info['author'] = match.group(1).strip()
                break
        
        # Extrahera datum
        date_patterns = [
            r'<time[^>]*datetime=["\']([^"\']+)',
            r'<meta[^>]*property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)',
            r'<meta[^>]*name=["\']date["\'][^>]*content=["\']([^"\']+)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                info['publication_date'] = match.group(1).strip()
                break
        
        # Extrahera beskrivning
        desc_patterns = [
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)',
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                info['description'] = match.group(1).strip()
                break
        
        # Extrahera nyckelord
        keywords_match = re.search(
            r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']+)',
            html_content, re.IGNORECASE
        )
        if keywords_match:
            info['keywords'] = [kw.strip() for kw in keywords_match.group(1).split(',')]
        
        return info
    
    def _immediate_pressreader_lookup(self, article_info: Dict[str, Any], session_id: str = None) -> Optional[Dict[str, Any]]:
        """Omedelbar lookup i PressReader när låst artikel detekteras"""
        if not self.api_key:
            logger.warning("API-nyckel saknas för PressReader-lookup")
            return None
        
        if not article_info.get('title'):
            logger.warning("Ingen titel att söka på")
            return None
        
        try:
            # Skapa sökförfrågan
            search_request = SearchRequest(
                query=article_info['title'],
                countries=self.config.get('default_countries', ['SE']),
                languages=self.config.get('default_languages', ['sv']),
                searchIn='header'  # Sök först i rubriker
            )
            
            # Utför sökning
            results = self._search_pressreader(search_request)
            
            if not results:
                # Försök med bredare sökning
                search_request.searchIn = 'everywhere'
                results = self._search_pressreader(search_request)
            
            if results:
                # Hitta bästa match
                best_match = self._find_best_match(article_info, results)
                
                if best_match and best_match['match_score'] >= self.config.get('match_threshold', 0.75):
                    # Spara matchning
                    self._save_article_match(ArticleMatch(
                        original_url=article_info['url'],
                        pressreader_article=best_match['article'],
                        match_score=best_match['match_score'],
                        matched_at=datetime.now(),
                        session_id=session_id or 'anonymous'
                    ))
                    
                    logger.info(f"Omedelbar PressReader-match hittad: {best_match['match_score']:.2f}")
                    return best_match
            
        except Exception as e:
            logger.error(f"Fel vid omedelbar PressReader-lookup: {e}")
        
        return None
    
    def _search_pressreader(self, search_request: SearchRequest) -> List[Dict[str, Any]]:
        """
        Sök i PressReader med korrekt POST-implementation
        """
        if not self.api_key:
            logger.error("API-nyckel saknas")
            return []
        
        # Kontrollera cache först
        cache_key = self._generate_cache_key(search_request)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info("Använder cached resultat")
            return cached_result
        
        # Endpoint enligt OpenAPI spec
        endpoint = f"{self.base_url}/discovery/v1/search"
        
        # POST-parametrar
        params = {
            'sort': 'relevance',
            'offset': 0,
            'limit': self.config.get('max_search_results', 20)
        }
        
        # Request body enligt OpenAPI spec
        request_body = {
            'query': search_request.query,
            'countries': search_request.countries,
            'itemTypes': search_request.itemTypes
        }
        
        # Lägg till valfria parametrar
        if search_request.author:
            request_body['author'] = search_request.author
        if search_request.cids:
            request_body['cids'] = search_request.cids
        if search_request.languages:
            request_body['languages'] = search_request.languages
        if search_request.searchIn:
            request_body['searchIn'] = search_request.searchIn
        if search_request.startDate:
            request_body['startDate'] = search_request.startDate
        if search_request.endDate:
            request_body['endDate'] = search_request.endDate
        
        try:
            logger.info(f"Söker i PressReader: {search_request.query}")
            
            response = self.session.post(
                endpoint,
                params=params,
                json=request_body,
                timeout=self.config.get('search_timeout', 30)
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extrahera artiklar enligt OpenAPI spec
            articles = []
            for item in data.get('items', []):
                if item.get('article'):
                    articles.append(item)
            
            # Cacha resultat
            if self.config.get('enable_caching', True):
                self._cache_result(cache_key, articles)
            
            logger.info(f"Hittade {len(articles)} artiklar")
            return articles
            
        except requests.RequestException as e:
            logger.error(f"Fel vid PressReader-sökning: {e}")
            return []
    
    def _find_best_match(self, article_info: Dict[str, Any], search_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Hitta bästa matchning bland sökresultaten"""
        best_match = None
        best_score = 0.0
        
        for result in search_results:
            article = result.get('article', {})
            if not article:
                continue
            
            score = self._calculate_match_score(article_info, article, result)
            
            if score > best_score:
                best_score = score
                best_match = {
                    'article': article,
                    'match_score': score,
                    'search_result': result
                }
        
        return best_match
    
    def _calculate_match_score(self, original: Dict[str, Any], pressreader_article: Dict[str, Any], full_result: Dict[str, Any]) -> float:
        """Avancerad matchningsscore-beräkning"""
        score = 0.0
        
        # Titel-matching (50% vikt)
        if original.get('title') and pressreader_article.get('title'):
            title_score = self._text_similarity(
                original['title'].lower(),
                pressreader_article['title'].lower()
            )
            score += title_score * 0.5
        
        # Författar-matching (25% vikt)
        if original.get('author') and pressreader_article.get('author'):
            author_score = self._text_similarity(
                original['author'].lower(),
                pressreader_article['author'].lower()
            )
            score += author_score * 0.25
        
        # Datum-matching (15% vikt)
        if original.get('publication_date') and full_result.get('issue', {}).get('date'):
            date_score = self._date_similarity(
                original['publication_date'],
                full_result['issue']['date']
            )
            score += date_score * 0.15
        
        # Innehålls-matching (10% vikt)
        if original.get('description') and full_result.get('summary'):
            content_score = self._text_similarity(
                original['description'].lower(),
                full_result['summary'].lower()
            )
            score += content_score * 0.1
        
        return score
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Beräkna textsimilaritet med förbättrad algoritm"""
        if not text1 or not text2:
            return 0.0
        
        # Rensa text
        text1 = re.sub(r'[^\w\s]', '', text1)
        text2 = re.sub(r'[^\w\s]', '', text2)
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        jaccard = intersection / union if union > 0 else 0.0
        
        # Substring similarity
        substring_score = 0.0
        if text1 in text2 or text2 in text1:
            substring_score = 0.5
        
        return (jaccard * 0.7) + (substring_score * 0.3)
    
    def _date_similarity(self, date1: str, date2: str) -> float:
        """Beräkna datumsimilaritet"""
        try:
            d1 = self._parse_date(date1)
            d2 = self._parse_date(date2)
            
            if d1 and d2:
                diff_days = abs((d1 - d2).days)
                if diff_days == 0:
                    return 1.0
                elif diff_days <= 1:
                    return 0.8
                elif diff_days <= 7:
                    return 0.6
                elif diff_days <= 30:
                    return 0.4
                else:
                    return 0.0
        except Exception:
            pass
        
        return 0.0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parsa datum från olika format"""
        if not date_str:
            return None
        
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d.%m.%Y',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str[:len(fmt)], fmt)
            except ValueError:
                continue
        
        return None
    
    def _generate_cache_key(self, search_request: SearchRequest) -> str:
        """Generera cache-nyckel för sökförfrågan"""
        request_dict = asdict(search_request)
        request_str = json.dumps(request_dict, sort_keys=True)
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Hämta cached resultat"""
        if not self.config.get('enable_caching', True):
            return None
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT results FROM search_cache 
            WHERE query_hash = ? AND expires_at > ?
        ''', (cache_key, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        
        return None
    
    def _cache_result(self, cache_key: str, results: List[Dict[str, Any]]):
        """Cacha sökresultat"""
        expires_at = datetime.now() + timedelta(seconds=self.config.get('cache_timeout', 3600))
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO search_cache 
            (query_hash, query_params, results, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (cache_key, '', json.dumps(results), datetime.now(), expires_at))
        
        conn.commit()
        conn.close()
    
    def _save_article_match(self, match: ArticleMatch):
        """Spara artikel-matchning"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO article_matches 
            (original_url, pressreader_article, match_score, matched_at, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            match.original_url,
            json.dumps(match.pressreader_article),
            match.match_score,
            match.matched_at,
            match.session_id
        ))
        
        conn.commit()
        conn.close()
    
    def _update_session_activity(self, session_id: str):
        """Uppdatera session-aktivitet"""
        with self.session_lock:
            if session_id in self.user_sessions:
                session = self.user_sessions[session_id]
                session.last_activity = datetime.now()
                session.total_checks += 1
                self._save_user_session(session)
    
    def get_user_statistics(self, session_id: str) -> Dict[str, Any]:
        """Hämta användarstatistik"""
        with self.session_lock:
            session = self.user_sessions.get(session_id)
            if not session:
                return {}
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Hämta matchningsstatistik
        cursor.execute('''
            SELECT COUNT(*), AVG(match_score), MAX(match_score)
            FROM article_matches WHERE session_id = ?
        ''', (session_id,))
        
        match_stats = cursor.fetchone()
        
        # Hämta aktivitetsstatistik
        cursor.execute('''
            SELECT action, COUNT(*) FROM activity_log 
            WHERE session_id = ? GROUP BY action
        ''', (session_id,))
        
        activity_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'session_info': asdict(session),
            'matches': {
                'total': match_stats[0] or 0,
                'average_score': match_stats[1] or 0.0,
                'best_score': match_stats[2] or 0.0
            },
            'activities': activity_stats
        }
    
    def batch_check_articles(self, urls: List[str], session_id: str = None) -> List[Dict[str, Any]]:
        """Batch-kontroll av flera artiklar samtidigt"""
        if session_id:
            self._log_activity(session_id, "batch_check_started", {"url_count": len(urls)})
        
        results = []
        
        # Använd concurrent futures för parallell bearbetning
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.get('concurrent_searches', 5)) as executor:
            future_to_url = {
                executor.submit(self.is_article_locked, url, session_id): url 
                for url in urls
            }
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Fel vid kontroll av {url}: {e}")
                    results.append({
                        'url': url,
                        'error': str(e),
                        'is_locked': False
                    })
        
        if session_id:
            self._log_activity(session_id, "batch_check_completed", {
                "total_urls": len(urls),
                "locked_articles": sum(1 for r in results if r.get('is_locked')),
                "pressreader_matches": sum(1 for r in results if r.get('pressreader_available'))
            })
        
        return results
    
    def create_config_file(self):
        """Skapa konfigurationsfil"""
        config = {
            "api_key": "DIN_PRESSREADER_API_NYCKEL",
            "max_search_results": 20,
            "search_timeout": 30,
            "cache_timeout": 3600,
            "default_countries": ["SE", "NO", "DK", "FI"],
            "default_languages": ["sv", "en", "no", "da"],
            "match_threshold": 0.75,
            "concurrent_searches": 5,
            "rate_limit_per_hour": 1000,
            "user_session_timeout": 1800,
            "enable_logging": True,
            "enable_caching": True
        }
        
        with open('pressreader_enhanced_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("Konfigurationsfil skapad: pressreader_enhanced_config.json")

def main():
    """Huvudfunktion för kommandoradsanvändning"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced PressReader Article Access")
    parser.add_argument('--create-config', action='store_true', help='Skapa konfigurationsfil')
    parser.add_argument('--check-url', help='Kontrollera specifik URL')
    parser.add_argument('--batch-check', nargs='+', help='Kontrollera flera URL:er')
    parser.add_argument('--session-id', help='Användarsession-ID')
    parser.add_argument('--stats', action='store_true', help='Visa statistik')
    parser.add_argument('--verbose', '-v', action='store_true', help='Detaljerad output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.create_config:
        client = EnhancedPressReaderClient()
        client.create_config_file()
        return
    
    # Initiera klient
    client = EnhancedPressReaderClient()
    
    # Skapa session om ingen angiven
    session_id = args.session_id or client.create_user_session()
    
    if args.check_url:
        result = client.is_article_locked(args.check_url, session_id)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    elif args.batch_check:
        results = client.batch_check_articles(args.batch_check, session_id)
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    
    elif args.stats:
        stats = client.get_user_statistics(session_id)
        print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()