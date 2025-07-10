// ==UserScript==
// @name            Swedish News Article Unlocker
// @version         3.0.0
// @description     Production-ready paywall detection with real PressReader API integration and intelligent fallback
// @author          Isak Skogstad
// @match           *://www.svd.se/*
// @match           *://svd.se/*
// @match           *://www.kungalvsposten.se/*
// @match           *://kungalvsposten.se/*
// @grant           none
// @run-at          document-end
// ==/UserScript==

(function() {
    'use strict';

    class SwedishNewsUnlocker {
        constructor() {
            this.apiUrl = 'http://localhost:8000/api/v2';
            this.sessionId = null;
            this.button = null;
            this.isProcessing = false;
            this.buttonTimer = null;
            this.currentSite = this.detectSite();
            
            this.init();
        }

        detectSite() {
            const hostname = window.location.hostname;
            if (hostname.includes('svd.se')) return 'svd';
            if (hostname.includes('kungalvsposten.se')) return 'kungalvsposten';
            return 'unknown';
        }

        async init() {
            // Skapa session tyst i bakgrunden
            await this.createSession();
            
            // Kontrollera för paywall baserat på site
            this.checkForPaywall();
            
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
                }
            } catch (error) {
                // Tyst fel - ingen användarinteraktion
            }
        }

        checkForPaywall() {
            let paywallDetected = false;
            
            if (this.currentSite === 'svd') {
                // SVD: Extensive paywall detection
                console.log('[SVD Debug] Startar paywall-detektion...');
                
                // 1. Meta-tags för paywall
                const paywallMeta = document.querySelector('meta[property="lp:paywall"]');
                const premiumMeta = document.querySelector('meta[property="lp:type"]');
                const paywallUserMeta = document.querySelector('meta[property="lp:paywall_user"]');
                
                // 2. DOM-element selektorer
                const svdPaywallSelectors = [
                    '[data-paywall]',
                    '.paywall',
                    '[class*="paywall"]',
                    '[class*="premium"]',
                    '[class*="subscriber"]',
                    '[class*="locked"]'
                ];
                
                const hasPaywallElements = svdPaywallSelectors.some(selector => 
                    document.querySelector(selector)
                );
                
                // 3. Textbaserad detektion
                const pageText = document.body.innerText.toLowerCase();
                const paywallTexts = [
                    'för att läsa hela artikeln',
                    'logga in för att läsa',
                    'prenumerera för att läsa',
                    'bli prenumerant',
                    'premium-artikel',
                    'plus-artikel'
                ];
                
                const hasPaywallText = paywallTexts.some(text => pageText.includes(text));
                
                // 4. URL-baserad detektion (SVD använder /a/ för artiklar)
                const isPremiumUrl = window.location.pathname.includes('/a/');
                
                // 5. Schema.org markup för betalinnehåll
                const schemaPaywall = document.querySelector('[typeof*="paywall"], [typeof*="premium"]');
                
                const detectionResults = {
                    paywallMeta: !!paywallMeta,
                    paywallMetaContent: paywallMeta?.content,
                    premiumMeta: !!premiumMeta,
                    premiumMetaContent: premiumMeta?.content,
                    paywallUserMeta: !!paywallUserMeta,
                    paywallUserContent: paywallUserMeta?.content,
                    hasPaywallElements,
                    hasPaywallText,
                    isPremiumUrl,
                    schemaPaywall: !!schemaPaywall
                };
                
                // Detektera paywall om något av följande är sant:
                if (paywallMeta || premiumMeta || hasPaywallElements || hasPaywallText || schemaPaywall) {
                    paywallDetected = true;
                }
                
                console.log('[SVD Paywall] Detektionsresultat:', detectionResults);
                console.log('[SVD Paywall] Paywall detekterad:', paywallDetected);
                
                // Vänta några sekunder innan vi visar knappen för att låta paywall ladda
                if (paywallDetected) {
                    setTimeout(() => {
                        // Dubbelkolla om paywall fortfarande finns efter laddning
                        const recheckPaywall = document.querySelector('meta[property="lp:paywall"]') || 
                                             document.querySelector('meta[property="lp:type"]') ||
                                             paywallTexts.some(text => document.body.innerText.toLowerCase().includes(text)) ||
                                             hasPaywallElements;
                        
                        if (recheckPaywall) {
                            console.log('[SVD Debug] Paywall bekräftad efter 3s delay');
                            this.showUnlockButton();
                        } else {
                            console.log('[SVD Debug] Paywall försvann efter laddning - användare inloggad?');
                        }
                    }, 3000);
                    
                    // Förhindra omedelbar visning
                    return;
                }
            } 
            else if (this.currentSite === 'kungalvsposten') {
                // Kungälvsposten: Kontrollera för paywall i texten och vanliga paywall-element
                const pageText = document.body.innerText.toLowerCase();
                const hasPaywallText = pageText.includes('paywall') || 
                                     pageText.includes('prenumeration') || 
                                     pageText.includes('logga in');
                
                const paywallSelectors = [
                    '.paywall',
                    '[class*="paywall"]',
                    '.subscription',
                    '[class*="subscription"]',
                    '.premium',
                    '[class*="premium"]',
                    '[data-paywall]'
                ];
                
                const hasPaywallElements = paywallSelectors.some(selector => 
                    document.querySelector(selector)
                );
                
                if (hasPaywallText || hasPaywallElements) {
                    paywallDetected = true;
                }
            }
            
            if (paywallDetected) {
                setTimeout(() => {
                    // Dubbelkolla paywall efter delay
                    this.recheckAndShowButton();
                }, 3000);
            }
        }

        recheckAndShowButton() {
            if (this.currentSite === 'svd') {
                // Dubbelkolla om paywall fortfarande finns
                const paywallMeta = document.querySelector('meta[property="lp:paywall"]');
                const premiumMeta = document.querySelector('meta[property="lp:type"]');
                
                const paywallTexts = [
                    'för att läsa hela artikeln',
                    'logga in för att läsa',
                    'prenumerera för att läsa',
                    'bli prenumerant',
                    'premium-artikel',
                    'plus-artikel'
                ];
                
                const hasPaywallText = paywallTexts.some(text => 
                    document.body.innerText.toLowerCase().includes(text)
                );
                
                const svdPaywallSelectors = [
                    '[data-paywall]',
                    '.paywall',
                    '[class*="paywall"]',
                    '[class*="premium"]',
                    '[class*="subscriber"]',
                    '[class*="locked"]'
                ];
                
                const hasPaywallElements = svdPaywallSelectors.some(selector => 
                    document.querySelector(selector)
                );
                
                if (paywallMeta || premiumMeta || hasPaywallText || hasPaywallElements) {
                    console.log('[SVD Debug] Paywall bekräftad - visar knapp');
                    this.showUnlockButton();
                } else {
                    console.log('[SVD Debug] Ingen paywall - användare inloggad eller gratis artikel');
                }
            } else if (this.currentSite === 'kungalvsposten') {
                // Rechec för Kungälvsposten
                const pageText = document.body.innerText.toLowerCase();
                const hasPaywallText = pageText.includes('paywall') || 
                                     pageText.includes('prenumeration') || 
                                     pageText.includes('logga in');
                
                if (hasPaywallText) {
                    this.showUnlockButton();
                }
            }
        }

        showUnlockButton() {
            if (this.button) return; // Knapp redan visad

            // Skapa grön knapp med site-specifik text
            const buttonText = this.currentSite === 'kungalvsposten' ? 'Hämta från PressReader' : 'Hämta artikel';
            
            this.button = document.createElement('div');
            this.button.id = 'news-unlock-button';
            this.button.innerHTML = `
                <div style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #28a745, #20692e);
                    color: white;
                    padding: 12px 18px;
                    border-radius: 8px;
                    box-shadow: 0 3px 15px rgba(40,167,69,0.4);
                    cursor: pointer;
                    z-index: 10000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    border: none;
                    min-width: 220px;
                    text-align: center;
                    animation: slideIn 0.5s ease-out;
                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span>${buttonText}</span>
                    </div>
                </div>
                <style>
                    @keyframes slideIn {
                        from {
                            transform: translateX(100%);
                            opacity: 0;
                        }
                        to {
                            transform: translateX(0);
                            opacity: 1;
                        }
                    }
                    @keyframes fadeOut {
                        from {
                            opacity: 1;
                            transform: translateX(0);
                        }
                        to {
                            opacity: 0;
                            transform: translateX(100%);
                        }
                    }
                </style>
            `;

            this.button.addEventListener('click', () => this.unlockArticle());
            document.body.appendChild(this.button);

            // Automatiskt dölj knappen efter 15 sekunder
            this.buttonTimer = setTimeout(() => {
                this.hideUnlockButton();
            }, 15000);
        }

        async unlockArticle() {
            if (this.isProcessing) return;
            
            this.isProcessing = true;
            this.hideUnlockButton();
            
            this.showNotification('Hämtar artikel...', 'loading');
            
            try {
                // Extrahera artikeldata från sidan för bättre sökning
                const articleData = this.extractArticleData();
                
                // Försök flera sökstrategier
                const searchStrategies = this.generateSearchStrategies(articleData);
                
                let foundArticle = null;
                for (const strategy of searchStrategies) {
                    this.showNotification(`Söker: ${strategy.name}...`, 'loading');
                    
                    const result = await this.searchWithStrategy(strategy);
                    if (result.success && result.data.pressreader_available) {
                        foundArticle = result.data;
                        break;
                    }
                    
                    // Kort paus mellan sökningar
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
                
                if (foundArticle) {
                    const article = foundArticle.pressreader_match.article;
                    
                    if (this.currentSite === 'kungalvsposten' && article.url) {
                        this.showNotification('Öppnar artikel i PressReader...', 'success');
                        setTimeout(() => {
                            window.open(article.url, '_blank');
                        }, 1000);
                    } else {
                        this.showNotification('Artikel hittad!', 'success');
                        setTimeout(() => {
                            this.displayArticle(foundArticle.pressreader_match);
                        }, 1000);
                    }
                } else {
                    this.showNotification('Artikeln finns inte tillgänglig', 'error');
                }
                
            } catch (error) {
                this.showNotification('Kunde inte hämta artikel', 'error');
            } finally {
                this.isProcessing = false;
            }
        }

        extractArticleData() {
            // Extrahera titel från olika möjliga selektorer
            const titleSelectors = [
                'h1',
                '[class*="title"]',
                '[class*="headline"]',
                '[class*="rubrik"]',
                'title',
                '[property="og:title"]',
                '[name="twitter:title"]'
            ];
            
            let title = '';
            for (const selector of titleSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    title = element.textContent || element.content || '';
                    if (title.length > 10) break; // Använd första meningsfulla titel
                }
            }
            
            // Extrahera ingress/sammanfattning
            const summarySelectors = [
                '[class*="ingress"]',
                '[class*="summary"]',
                '[class*="excerpt"]',
                '[class*="lead"]',
                '[property="og:description"]',
                '[name="description"]'
            ];
            
            let summary = '';
            for (const selector of summarySelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    summary = element.textContent || element.content || '';
                    if (summary.length > 20) break;
                }
            }
            
            // Extrahera författare
            const authorSelectors = [
                '[class*="author"]',
                '[class*="byline"]',
                '[rel="author"]',
                '[class*="journalist"]'
            ];
            
            let author = '';
            for (const selector of authorSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    author = element.textContent || '';
                    if (author.length > 3) break;
                }
            }
            
            // Extrahera publikationsdatum
            const dateSelectors = [
                '[class*="date"]',
                '[class*="published"]',
                '[datetime]',
                'time',
                '[property="article:published_time"]'
            ];
            
            let publishDate = '';
            for (const selector of dateSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    publishDate = element.textContent || element.datetime || element.content || '';
                    if (publishDate.length > 5) break;
                }
            }
            
            return {
                title: this.cleanText(title),
                summary: this.cleanText(summary),
                author: this.cleanText(author),
                publishDate: this.cleanText(publishDate),
                url: window.location.href,
                site: this.currentSite
            };
        }

        cleanText(text) {
            return text
                .replace(/\s+/g, ' ')
                .replace(/[^\w\såäöÅÄÖ-]/g, '')
                .trim()
                .substring(0, 200); // Begränsa längd
        }

        generateSearchStrategies(articleData) {
            const strategies = [];
            const publicationName = this.getPublicationName();
            
            // Strategi 1: Titel + Publikation + Datum (Print version mapping)
            if (articleData.title && publicationName && articleData.publishDate) {
                const date = this.normalizeDate(articleData.publishDate);
                strategies.push({
                    name: 'Titel + Publikation + Datum',
                    query: `"${articleData.title}" AND "${publicationName}" AND "${date}"`,
                    searchData: {
                        ...articleData,
                        publication: publicationName,
                        search_query: `"${articleData.title}" AND "${publicationName}" AND "${date}"`
                    }
                });
            }
            
            // Strategi 2: Titel + Publikation (utan exakt datum)
            if (articleData.title && publicationName) {
                strategies.push({
                    name: 'Titel + Publikation',
                    query: `"${articleData.title}" AND "${publicationName}"`,
                    searchData: {
                        ...articleData,
                        publication: publicationName,
                        search_query: `"${articleData.title}" AND "${publicationName}"`
                    }
                });
            }
            
            // Strategi 3: Nyckelord + Publikation (för tryckt vs digital mapping)
            if (articleData.title && publicationName) {
                const keywords = this.extractKeywords(articleData.title);
                if (keywords.length >= 2) {
                    const keywordQuery = keywords.slice(0, 3).join(' AND ');
                    strategies.push({
                        name: 'Nyckelord + Publikation',
                        query: `(${keywordQuery}) AND "${publicationName}"`,
                        searchData: {
                            ...articleData,
                            publication: publicationName,
                            search_query: `(${keywordQuery}) AND "${publicationName}"`
                        }
                    });
                }
            }
            
            // Strategi 4: Författare + Publikation + Datum
            if (articleData.author && publicationName && articleData.publishDate) {
                const date = this.normalizeDate(articleData.publishDate);
                strategies.push({
                    name: 'Författare + Publikation + Datum',
                    query: `"${articleData.author}" AND "${publicationName}" AND "${date}"`,
                    searchData: {
                        ...articleData,
                        publication: publicationName,
                        search_query: `"${articleData.author}" AND "${publicationName}" AND "${date}"`
                    }
                });
            }
            
            // Strategi 5: Exakt titel (fallback)
            if (articleData.title) {
                strategies.push({
                    name: 'Exakt titel',
                    query: `"${articleData.title}"`,
                    searchData: {
                        ...articleData,
                        search_query: `"${articleData.title}"`
                    }
                });
            }
            
            // Strategi 6: Wildcard + Publikation
            if (articleData.title && publicationName) {
                const mainWords = this.extractKeywords(articleData.title).slice(0, 3);
                if (mainWords.length > 0) {
                    const wildcardQuery = mainWords.map(word => `${word}*`).join(' AND ');
                    strategies.push({
                        name: 'Wildcard + Publikation',
                        query: `(${wildcardQuery}) AND "${publicationName}"`,
                        searchData: {
                            ...articleData,
                            publication: publicationName,
                            search_query: `(${wildcardQuery}) AND "${publicationName}"`
                        }
                    });
                }
            }
            
            // Strategi 7: URL-baserad sökning (sista utväg)
            strategies.push({
                name: 'URL-baserad',
                query: 'url_search',
                searchData: {
                    url: articleData.url
                }
            });
            
            return strategies;
        }

        getPublicationName() {
            const siteToPublication = {
                'svd': 'Svenska Dagbladet',
                'kungalvsposten': 'Kungälvs-Posten'
            };
            return siteToPublication[this.currentSite] || '';
        }

        normalizeDate(dateString) {
            // Försök att konvertera olika datumformat till PressReader-format
            try {
                const date = new Date(dateString);
                if (isNaN(date.getTime())) {
                    // Försök att extrahera datum från text
                    const swedishMonths = {
                        'januari': '01', 'februari': '02', 'mars': '03', 'april': '04',
                        'maj': '05', 'juni': '06', 'juli': '07', 'augusti': '08',
                        'september': '09', 'oktober': '10', 'november': '11', 'december': '12',
                        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                        'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
                        'okt': '10', 'nov': '11', 'dec': '12'
                    };
                    
                    // Sök efter svenska datumformat
                    for (const [month, num] of Object.entries(swedishMonths)) {
                        if (dateString.toLowerCase().includes(month)) {
                            const year = dateString.match(/20\d{2}/)?.[0] || new Date().getFullYear();
                            const day = dateString.match(/\b(\d{1,2})\b/)?.[0]?.padStart(2, '0') || '01';
                            return `${day} ${this.getSwedishMonthName(num)} ${year}`;
                        }
                    }
                }
                
                // Standard datum format för PressReader
                const day = date.getDate().toString().padStart(2, '0');
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                const year = date.getFullYear();
                
                return `${day} ${this.getSwedishMonthName(month)} ${year}`;
            } catch (error) {
                // Returnera dagens datum som fallback
                const today = new Date();
                const day = today.getDate().toString().padStart(2, '0');
                const month = (today.getMonth() + 1).toString().padStart(2, '0');
                const year = today.getFullYear();
                return `${day} ${this.getSwedishMonthName(month)} ${year}`;
            }
        }

        getSwedishMonthName(monthNumber) {
            const months = {
                '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
                '05': 'Maj', '06': 'Jun', '07': 'Jul', '08': 'Aug',
                '09': 'Sep', '10': 'Okt', '11': 'Nov', '12': 'Dec'
            };
            return months[monthNumber] || monthNumber;
        }

        extractKeywords(text) {
            // Ta bort vanliga svenska stoppord
            const stopWords = [
                'och', 'eller', 'men', 'att', 'som', 'för', 'på', 'av', 'till', 'från',
                'med', 'vid', 'om', 'i', 'åt', 'under', 'över', 'utan', 'mellan',
                'genom', 'efter', 'före', 'sedan', 'då', 'när', 'var', 'här', 'där',
                'den', 'det', 'de', 'dem', 'dessa', 'detta', 'då', 'nu', 'så',
                'en', 'ett', 'är', 'var', 'har', 'hade', 'ska', 'skulle', 'kan', 'kunde'
            ];
            
            return text
                .toLowerCase()
                .split(/\s+/)
                .filter(word => 
                    word.length > 3 && 
                    !stopWords.includes(word) &&
                    /^[a-zåäö]+$/.test(word)
                )
                .slice(0, 5); // Max 5 nyckelord
        }

        async searchWithStrategy(strategy) {
            try {
                const response = await fetch(`${this.apiUrl}/check-article`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        ...strategy.searchData,
                        session_id: this.sessionId
                    })
                });
                
                const data = await response.json();
                return {
                    success: true,
                    data: data.result || data,
                    strategy: strategy.name
                };
                
            } catch (error) {
                return {
                    success: false,
                    error: error.message,
                    strategy: strategy.name
                };
            }
        }

        showNotification(message, type) {
            // Ta bort eventuell befintlig notifikation
            const existing = document.getElementById('svd-notification');
            if (existing) existing.remove();

            const notification = document.createElement('div');
            notification.id = 'svd-notification';
            
            const colors = {
                loading: '#007bff',
                success: '#28a745',
                error: '#dc3545'
            };
            
            notification.innerHTML = `
                <div style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${colors[type]};
                    color: white;
                    padding: 12px 18px;
                    border-radius: 6px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    z-index: 10001;
                    box-shadow: 0 3px 15px rgba(0,0,0,0.2);
                    animation: slideIn 0.3s ease-out;
                ">
                    ${type === 'loading' ? '<span style="margin-right: 8px;">⏳</span>' : ''}
                    ${message}
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Automatiskt dölj efter 3 sekunder (utom för loading)
            if (type !== 'loading') {
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 3000);
            }
        }

        hideUnlockButton() {
            if (this.buttonTimer) {
                clearTimeout(this.buttonTimer);
                this.buttonTimer = null;
            }
            if (this.button) {
                this.button.style.animation = 'fadeOut 0.3s ease-out forwards';
                setTimeout(() => {
                    if (this.button) {
                        this.button.remove();
                        this.button = null;
                    }
                }, 300);
            }
        }

        displayArticle(matchData) {
            const article = matchData.article;
            const searchResult = matchData.search_result;
            
            // Ta bort eventuell notifikation
            const notification = document.getElementById('svd-notification');
            if (notification) notification.remove();
            
            // Skapa artikel-container
            const articleContainer = document.createElement('div');
            articleContainer.id = 'svd-article-container';
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
                            <span style="font-weight: 600; color: #28a745;">📰 Artikel hämtad</span>
                        </div>
                        
                        <button id="close-article" style="
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
                    
                    <div style="
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 40px 20px;
                        line-height: 1.6;
                    ">
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
                            font-size: 16px;
                            line-height: 1.8;
                            color: #333;
                        ">
                            ${article.full_content || searchResult.summary || 'Artikelinnehåll tillgängligt.'}
                        </div>
                    </div>
                </div>
            `;
            
            const closeButton = articleContainer.querySelector('#close-article');
            closeButton.addEventListener('click', () => {
                articleContainer.remove();
            });
            
            const escHandler = (e) => {
                if (e.key === 'Escape' && articleContainer.parentNode) {
                    articleContainer.remove();
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
            
            document.body.appendChild(articleContainer);
        }

        observePageChanges() {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        setTimeout(() => this.checkForPaywall(), 1000);
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    // Initiera på SVD och Kungälvsposten sidor
    const hostname = window.location.hostname;
    if (hostname.includes('svd.se') || hostname.includes('kungalvsposten.se')) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                new SwedishNewsUnlocker();
            });
        } else {
            new SwedishNewsUnlocker();
        }
    }

})();