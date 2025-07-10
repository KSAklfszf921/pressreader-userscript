#!/usr/bin/env python3
"""
Enhanced PressReader Server
===========================

Webbserver för Enhanced PressReader Article Access System med:
- RESTful API endpoints
- WebSocket för real-time updates
- Användarsession-hantering
- Statistik och monitoring
- Batch-bearbetning
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import uuid

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from pressreader_enhanced import EnhancedPressReaderClient, UserSession

# Konfigurera logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic modeller för API
class ArticleCheckRequest(BaseModel):
    url: str = Field(..., description="URL till artikel som ska kontrolleras")
    session_id: Optional[str] = Field(None, description="Användarsession-ID")

class BatchCheckRequest(BaseModel):
    urls: List[str] = Field(..., description="Lista med URL:er att kontrollera")
    session_id: Optional[str] = Field(None, description="Användarsession-ID")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Sökfråga")
    countries: Optional[List[str]] = Field(None, description="Länder att söka i")
    languages: Optional[List[str]] = Field(None, description="Språk att söka på")
    author: Optional[str] = Field(None, description="Författare")
    session_id: Optional[str] = Field(None, description="Användarsession-ID")

class UserSessionRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="Användar-ID")

# Global client instance
client = EnhancedPressReaderClient()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connection established for session: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket connection closed for session: {session_id}")
    
    async def send_personal_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

# FastAPI app
app = FastAPI(
    title="Enhanced PressReader API",
    description="Avancerad API för PressReader artikel-åtkomst med användarspårning och real-time updates",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Enkel autentisering (kan utökas)"""
    return credentials.credentials if credentials else None

@app.on_event("startup")
async def startup_event():
    """Startup-händelser"""
    logger.info("Enhanced PressReader Server startar...")
    
    # Skapa konfigurationsfil om den inte finns
    try:
        client.create_config_file()
        logger.info("Konfigurationsfil kontrollerad")
    except Exception as e:
        logger.warning(f"Kunde inte skapa konfigurationsfil: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown-händelser"""
    logger.info("Enhanced PressReader Server stängs av...")

# API Endpoints

@app.post("/api/v2/sessions", response_model=dict)
async def create_session(request: UserSessionRequest):
    """Skapa ny användarsession"""
    try:
        session_id = client.create_user_session(request.user_id)
        return {
            "success": True,
            "session_id": session_id,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Fel vid session-skapande: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/sessions/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Hämta session-statistik"""
    try:
        stats = client.get_user_statistics(session_id)
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Fel vid hämtning av statistik: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/check-article")
async def check_article(request: ArticleCheckRequest, background_tasks: BackgroundTasks):
    """Kontrollera om artikel är låst och tillgänglig via PressReader"""
    try:
        # Kör kontroll i bakgrunden för snabbare respons
        result = client.is_article_locked(request.url, request.session_id)
        
        # Skicka real-time update via WebSocket
        if request.session_id:
            background_tasks.add_task(
                manager.send_personal_message,
                {
                    "type": "article_check_completed",
                    "data": result
                },
                request.session_id
            )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Fel vid artikel-kontroll: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/batch-check")
async def batch_check_articles(request: BatchCheckRequest, background_tasks: BackgroundTasks):
    """Kontrollera flera artiklar samtidigt"""
    try:
        # Notifiera start via WebSocket
        if request.session_id:
            await manager.send_personal_message(
                {
                    "type": "batch_check_started",
                    "data": {"total_urls": len(request.urls)}
                },
                request.session_id
            )
        
        # Kör batch-kontroll
        results = client.batch_check_articles(request.urls, request.session_id)
        
        # Skicka slutresultat via WebSocket
        if request.session_id:
            background_tasks.add_task(
                manager.send_personal_message,
                {
                    "type": "batch_check_completed",
                    "data": {
                        "results": results,
                        "summary": {
                            "total": len(results),
                            "locked": sum(1 for r in results if r.get('is_locked')),
                            "pressreader_available": sum(1 for r in results if r.get('pressreader_available'))
                        }
                    }
                },
                request.session_id
            )
        
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        logger.error(f"Fel vid batch-kontroll: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/search")
async def search_pressreader(request: SearchRequest):
    """Sök direkt i PressReader"""
    try:
        from pressreader_enhanced import SearchRequest as PRSearchRequest
        
        pr_request = PRSearchRequest(
            query=request.query,
            countries=request.countries or client.config.get('default_countries', ['SE']),
            languages=request.languages or client.config.get('default_languages', ['sv']),
            author=request.author
        )
        
        results = client._search_pressreader(pr_request)
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Fel vid PressReader-sökning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/health")
async def health_check():
    """Hälsokontroll"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "pressreader_configured": client.api_key is not None
    }

@app.get("/api/v2/config")
async def get_config():
    """Hämta konfiguration (utan känslig data)"""
    safe_config = client.config.copy()
    
    # Ta bort känslig data
    safe_config.pop('api_key', None)
    
    return {
        "success": True,
        "config": safe_config
    }

# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket för real-time updates"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Håll anslutningen öppen och lyssna på meddelanden
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Hantera olika typer av meddelanden
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "get_stats":
                stats = client.get_user_statistics(session_id)
                await websocket.send_text(json.dumps({
                    "type": "stats_update",
                    "data": stats
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)

# Statiska filer och frontend
@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Enkel frontend för testing"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Enhanced PressReader API</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            .form-group { margin: 10px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, button { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #007bff; color: white; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; }
            .success { border-left: 4px solid #28a745; }
            .error { border-left: 4px solid #dc3545; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .status.connected { background: #d4edda; color: #155724; }
            .status.disconnected { background: #f8d7da; color: #721c24; }
            #log { height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Enhanced PressReader API - Test Interface</h1>
            
            <div class="section">
                <h2>Session Management</h2>
                <div class="form-group">
                    <button onclick="createSession()">Skapa ny session</button>
                    <div id="sessionInfo"></div>
                </div>
                <div class="form-group">
                    <div id="websocketStatus" class="status disconnected">WebSocket: Disconnected</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Artikel-kontroll</h2>
                <div class="form-group">
                    <label>Artikel-URL:</label>
                    <input type="url" id="articleUrl" placeholder="https://example.com/article">
                    <button onclick="checkArticle()">Kontrollera artikel</button>
                </div>
                <div class="form-group">
                    <label>Batch-kontroll (en URL per rad):</label>
                    <textarea id="batchUrls" rows="4" placeholder="https://example.com/article1\nhttps://example.com/article2"></textarea>
                    <button onclick="batchCheck()">Kontrollera batch</button>
                </div>
            </div>
            
            <div class="section">
                <h2>PressReader-sökning</h2>
                <div class="form-group">
                    <label>Sökfråga:</label>
                    <input type="text" id="searchQuery" placeholder="sverige ekonomi">
                    <button onclick="searchPressReader()">Sök</button>
                </div>
            </div>
            
            <div class="section">
                <h2>Statistik</h2>
                <button onclick="getStats()">Hämta statistik</button>
                <div id="statsResult"></div>
            </div>
            
            <div class="section">
                <h2>Real-time Log</h2>
                <div id="log"></div>
                <button onclick="clearLog()">Rensa log</button>
            </div>
        </div>
        
        <script>
            let currentSessionId = null;
            let websocket = null;
            
            function log(message) {
                const logDiv = document.getElementById('log');
                const timestamp = new Date().toLocaleTimeString();
                logDiv.innerHTML += `<div>[${timestamp}] ${message}</div>`;
                logDiv.scrollTop = logDiv.scrollHeight;
            }
            
            function clearLog() {
                document.getElementById('log').innerHTML = '';
            }
            
            async function createSession() {
                try {
                    const response = await fetch('/api/v2/sessions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        currentSessionId = data.session_id;
                        document.getElementById('sessionInfo').innerHTML = 
                            `<div class="result success">Session skapad: ${currentSessionId}</div>`;
                        connectWebSocket();
                        log(`Session skapad: ${currentSessionId}`);
                    }
                } catch (error) {
                    log(`Fel vid session-skapande: ${error.message}`);
                }
            }
            
            function connectWebSocket() {
                if (!currentSessionId) return;
                
                const wsUrl = `ws://localhost:8000/ws/${currentSessionId}`;
                websocket = new WebSocket(wsUrl);
                
                websocket.onopen = function() {
                    document.getElementById('websocketStatus').className = 'status connected';
                    document.getElementById('websocketStatus').textContent = 'WebSocket: Connected';
                    log('WebSocket ansluten');
                };
                
                websocket.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                    log(`WebSocket: ${message.type} - ${JSON.stringify(message.data).substring(0, 100)}...`);
                    
                    if (message.type === 'article_check_completed') {
                        showResult('articleResult', message.data);
                    } else if (message.type === 'batch_check_completed') {
                        showResult('batchResult', message.data);
                    }
                };
                
                websocket.onclose = function() {
                    document.getElementById('websocketStatus').className = 'status disconnected';
                    document.getElementById('websocketStatus').textContent = 'WebSocket: Disconnected';
                    log('WebSocket frånkopplad');
                };
                
                websocket.onerror = function(error) {
                    log(`WebSocket error: ${error}`);
                };
            }
            
            async function checkArticle() {
                const url = document.getElementById('articleUrl').value;
                if (!url) {
                    alert('Ange en URL');
                    return;
                }
                
                try {
                    const response = await fetch('/api/v2/check-article', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, session_id: currentSessionId })
                    });
                    
                    const data = await response.json();
                    showResult('articleResult', data);
                    log(`Artikel kontrollerad: ${url}`);
                } catch (error) {
                    log(`Fel vid artikel-kontroll: ${error.message}`);
                }
            }
            
            async function batchCheck() {
                const urlsText = document.getElementById('batchUrls').value;
                const urls = urlsText.split('\\n').filter(url => url.trim());
                
                if (urls.length === 0) {
                    alert('Ange minst en URL');
                    return;
                }
                
                try {
                    const response = await fetch('/api/v2/batch-check', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ urls, session_id: currentSessionId })
                    });
                    
                    const data = await response.json();
                    showResult('batchResult', data);
                    log(`Batch-kontroll startad: ${urls.length} URL:er`);
                } catch (error) {
                    log(`Fel vid batch-kontroll: ${error.message}`);
                }
            }
            
            async function searchPressReader() {
                const query = document.getElementById('searchQuery').value;
                if (!query) {
                    alert('Ange en sökfråga');
                    return;
                }
                
                try {
                    const response = await fetch('/api/v2/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, session_id: currentSessionId })
                    });
                    
                    const data = await response.json();
                    showResult('searchResult', data);
                    log(`PressReader-sökning: "${query}" - ${data.count} resultat`);
                } catch (error) {
                    log(`Fel vid sökning: ${error.message}`);
                }
            }
            
            async function getStats() {
                if (!currentSessionId) {
                    alert('Skapa en session först');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/v2/sessions/${currentSessionId}/stats`);
                    const data = await response.json();
                    document.getElementById('statsResult').innerHTML = 
                        `<div class="result success"><pre>${JSON.stringify(data.stats, null, 2)}</pre></div>`;
                    log('Statistik hämtad');
                } catch (error) {
                    log(`Fel vid statistik-hämtning: ${error.message}`);
                }
            }
            
            function showResult(elementId, data) {
                let element = document.getElementById(elementId);
                if (!element) {
                    element = document.createElement('div');
                    element.id = elementId;
                    document.body.appendChild(element);
                }
                
                element.innerHTML = `<div class="result success"><pre>${JSON.stringify(data, null, 2)}</pre></div>`;
            }
            
            // Auto-create session on load
            window.onload = function() {
                createSession();
            };
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(
        "pressreader_enhanced_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )