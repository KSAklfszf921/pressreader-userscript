// PressReader Browser Extension - Content Script
// Automatisk detektering och öppning av låsta artiklar

class PressReaderArticleUnlocker {
    constructor() {
        this.apiUrl = 'http://localhost:8000/api/v2';
        this.sessionId = null;
        this.button = null;
        this.progressOverlay = null;
        this.isProcessing = false;
        
        this.init();
    }

    async init() {
        console.log('PressReader Article Unlocker initialiserad');
        
        // Skapa session
        await this.createSession();
        
        // Kontrollera om sidan har låst innehåll
        this.checkForLockedContent();
        
        // Övervaka förändringar på sidan
        this.observePageChanges();
    }

    async createSession() {
        try {
            const response = await fetch(`${this.apiUrl}/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            if (data.success) {
                this.sessionId = data.session_id;
                console.log('Session skapad:', this.sessionId);
            }
        } catch (error) {
            console.error('Fel vid session-skapande:', error);
        }
    }

    checkForLockedContent() {
        // Vanliga indikatorer för låsta artiklar
        const lockIndicators = [
            'paywall', 'subscribe', 'subscription', 'premium', 'member only',
            'prenumerera', 'prenumeration', 'logga in', 'registrera',
            'betalvägg', 'låst innehåll', 'prenumerantexklusivt'
        ];

        const pageText = document.body.innerText.toLowerCase();
        const hasLockIndicators = lockIndicators.some(indicator => 
            pageText.includes(indicator)
        );

        // Kontrollera även för vanliga betalvägg-element
        const paywallElements = document.querySelectorAll([
            '[class*="paywall"]',
            '[class*="subscription"]',
            '[class*="premium"]',
            '[class*="locked"]',
            '[id*="paywall"]',
            '[id*="subscription"]'
        ].join(','));

        const hasPaywallElements = paywallElements.length > 0;

        if (hasLockIndicators || hasPaywallElements) {
            console.log('Låst innehåll detekterat');
            this.showUnlockButton();
        }
    }

    showUnlockButton() {
        if (this.button) return; // Knapp redan visad

        // Skapa knapp
        this.button = document.createElement('div');
        this.button.id = 'pressreader-unlock-button';
        this.button.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                padding: 15px 20px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,123,255,0.3);
                cursor: pointer;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s ease;
                border: none;
                min-width: 250px;
                text-align: center;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                    <span>Öppna med PressReader</span>
                </div>
                <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">
                    Klicka för att försöka låsa upp artikeln
                </div>
            </div>
        `;

        this.button.addEventListener('click', () => this.unlockArticle());
        document.body.appendChild(this.button);
    }

    async unlockArticle() {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        this.showProgressOverlay();
        
        try {
            // Steg 1: Kontrollera artikel
            this.updateProgress('Kontrollerar artikel...', 20);
            
            const checkResponse = await fetch(`${this.apiUrl}/check-article`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: window.location.href,
                    session_id: this.sessionId
                })
            });
            
            const checkData = await checkResponse.json();
            
            if (!checkData.success) {
                throw new Error('Kunde inte kontrollera artikel');
            }
            
            // Steg 2: Sök i PressReader
            this.updateProgress('Söker i PressReader...', 50);
            
            if (checkData.result.pressreader_available) {
                // Artikel hittad i PressReader
                this.updateProgress('Artikel hittad! Laddar innehåll...', 80);
                
                // Visa artikeln
                await this.displayPressReaderArticle(checkData.result.pressreader_match);
                
                this.updateProgress('Klart!', 100);
                
                setTimeout(() => {
                    this.hideProgressOverlay();
                    this.hideUnlockButton();
                }, 1000);
                
            } else {
                // Artikel inte hittad
                this.updateProgress('Artikeln finns inte i PressReader', 100);
                
                setTimeout(() => {
                    this.hideProgressOverlay();
                }, 3000);
            }
            
        } catch (error) {
            console.error('Fel vid upplåsning:', error);
            this.updateProgress(`Fel: ${error.message}`, 100);
            
            setTimeout(() => {
                this.hideProgressOverlay();
            }, 3000);
        } finally {
            this.isProcessing = false;
        }
    }

    showProgressOverlay() {
        // Skapa progress overlay
        this.progressOverlay = document.createElement('div');
        this.progressOverlay.id = 'pressreader-progress-overlay';
        this.progressOverlay.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 10001;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <div style="
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                    text-align: center;
                    min-width: 300px;
                    max-width: 400px;
                ">
                    <div style="
                        width: 60px;
                        height: 60px;
                        margin: 0 auto 20px;
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #007bff;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    "></div>
                    
                    <div id="progress-text" style="
                        font-size: 18px;
                        font-weight: 600;
                        color: #333;
                        margin-bottom: 20px;
                    ">Startar...</div>
                    
                    <div style="
                        width: 100%;
                        height: 8px;
                        background: #f0f0f0;
                        border-radius: 4px;
                        overflow: hidden;
                        margin-bottom: 10px;
                    ">
                        <div id="progress-bar" style="
                            height: 100%;
                            background: linear-gradient(90deg, #007bff, #0056b3);
                            width: 0%;
                            transition: width 0.3s ease;
                        "></div>
                    </div>
                    
                    <div id="progress-percentage" style="
                        font-size: 14px;
                        color: #666;
                    ">0%</div>
                </div>
            </div>
            
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        
        document.body.appendChild(this.progressOverlay);
    }

    updateProgress(text, percentage) {
        if (!this.progressOverlay) return;
        
        const progressText = this.progressOverlay.querySelector('#progress-text');
        const progressBar = this.progressOverlay.querySelector('#progress-bar');
        const progressPercentage = this.progressOverlay.querySelector('#progress-percentage');
        
        if (progressText) progressText.textContent = text;
        if (progressBar) progressBar.style.width = percentage + '%';
        if (progressPercentage) progressPercentage.textContent = percentage + '%';
    }

    hideProgressOverlay() {
        if (this.progressOverlay) {
            this.progressOverlay.remove();
            this.progressOverlay = null;
        }
    }

    hideUnlockButton() {
        if (this.button) {
            this.button.remove();
            this.button = null;
        }
    }

    async displayPressReaderArticle(matchData) {
        const article = matchData.article;
        const searchResult = matchData.search_result;
        
        // Skapa artikel-container
        const articleContainer = document.createElement('div');
        articleContainer.id = 'pressreader-article-container';
        articleContainer.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: white;
                z-index: 10002;
                overflow-y: auto;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <!-- Header -->
                <div style="
                    position: sticky;
                    top: 0;
                    background: white;
                    border-bottom: 1px solid #e0e0e0;
                    padding: 15px 20px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    z-index: 10003;
                ">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="#007bff">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        <span style="font-weight: 600; color: #007bff;">PressReader</span>
                        <span style="color: #666;">•</span>
                        <span style="font-size: 14px; color: #666;">Matchning: ${(matchData.match_score * 100).toFixed(0)}%</span>
                    </div>
                    
                    <button id="close-pressreader-article" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #666;
                        padding: 5px;
                        border-radius: 4px;
                    " onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">
                        ×
                    </button>
                </div>
                
                <!-- Artikel innehåll -->
                <div style="
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px 20px;
                    line-height: 1.6;
                ">
                    <div style="
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 8px;
                        border-left: 4px solid #007bff;
                        margin-bottom: 30px;
                    ">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">
                            ${searchResult.publication?.title || 'Okänd publikation'} • ${searchResult.issue?.date || 'Okänt datum'}
                        </div>
                        <div style="font-size: 12px; color: #007bff;">
                            Hittad via PressReader API
                        </div>
                    </div>
                    
                    <h1 style="
                        font-size: 32px;
                        font-weight: 700;
                        line-height: 1.2;
                        margin-bottom: 20px;
                        color: #1a1a1a;
                    ">${article.title || 'Titel saknas'}</h1>
                    
                    ${article.subTitle ? `
                        <h2 style="
                            font-size: 20px;
                            font-weight: 400;
                            color: #666;
                            margin-bottom: 20px;
                        ">${article.subTitle}</h2>
                    ` : ''}
                    
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 20px;
                        margin-bottom: 30px;
                        padding-bottom: 20px;
                        border-bottom: 1px solid #e0e0e0;
                    ">
                        ${article.author ? `
                            <div>
                                <span style="font-weight: 600;">Författare:</span>
                                <span style="color: #666;">${article.author}</span>
                            </div>
                        ` : ''}
                        
                        ${searchResult.issue?.date ? `
                            <div>
                                <span style="font-weight: 600;">Publicerad:</span>
                                <span style="color: #666;">${searchResult.issue.date}</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    ${searchResult.summary ? `
                        <div style="
                            font-size: 18px;
                            line-height: 1.6;
                            color: #333;
                            margin-bottom: 30px;
                            font-style: italic;
                        ">${searchResult.summary}</div>
                    ` : ''}
                    
                    <div style="
                        font-size: 16px;
                        line-height: 1.8;
                        color: #333;
                    ">
                        ${article.full_content || searchResult.summary || 'Artikelinnehåll inte tillgängligt via API.'}
                    </div>
                    
                    ${article.copyright ? `
                        <div style="
                            margin-top: 40px;
                            padding: 20px;
                            background: #f8f9fa;
                            border-radius: 8px;
                            font-size: 14px;
                            color: #666;
                        ">${article.copyright}</div>
                    ` : ''}
                    
                    <div style="
                        margin-top: 40px;
                        padding: 20px;
                        background: #e3f2fd;
                        border-radius: 8px;
                        text-align: center;
                    ">
                        <div style="font-size: 16px; font-weight: 600; margin-bottom: 10px;">
                            Läs fullständig artikel på PressReader
                        </div>
                        <a href="${article.url}" target="_blank" style="
                            display: inline-block;
                            background: #007bff;
                            color: white;
                            padding: 12px 24px;
                            text-decoration: none;
                            border-radius: 6px;
                            font-weight: 600;
                            transition: background 0.3s ease;
                        " onmouseover="this.style.background='#0056b3'" onmouseout="this.style.background='#007bff'">
                            Öppna i PressReader
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        // Lägg till stäng-funktionalitet
        const closeButton = articleContainer.querySelector('#close-pressreader-article');
        closeButton.addEventListener('click', () => {
            articleContainer.remove();
        });
        
        // Lägg till ESC-tangent för att stänga
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && articleContainer.parentNode) {
                articleContainer.remove();
            }
        });
        
        document.body.appendChild(articleContainer);
    }

    observePageChanges() {
        // Övervaka förändringar på sidan för SPA:er
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Kontrollera om ny låst innehåll har lagts till
                    setTimeout(() => this.checkForLockedContent(), 1000);
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}

// Initiera när sidan laddas
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PressReaderArticleUnlocker();
    });
} else {
    new PressReaderArticleUnlocker();
}

// Återinitiera vid navigering (för SPA:er)
window.addEventListener('popstate', () => {
    setTimeout(() => {
        new PressReaderArticleUnlocker();
    }, 1000);
});