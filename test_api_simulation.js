// ==UserScript==
// @name            Swedish News Article Unlocker (TEST VERSION)
// @namespace       https://github.com/quoid/userscripts
// @version         1.2.0-test
// @description     TEST VERSION - Simulates API responses for testing paywall detection
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

    class SwedishNewsUnlockerTest {
        constructor() {
            this.sessionId = 'test-session-' + Math.random().toString(36).substr(2, 9);
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
            console.log(`[TEST] Initialiserad på ${this.currentSite} med session: ${this.sessionId}`);
            
            // Simulera paywall-detektion efter kort delay
            setTimeout(() => {
                this.simulatePaywallDetection();
            }, 2000);
            
            this.observePageChanges();
        }

        simulatePaywallDetection() {
            // Simulera att en paywall alltid hittas för test
            console.log(`[TEST] Simulerar paywall-detektion på ${this.currentSite}`);
            this.showUnlockButton();
        }

        checkForPaywall() {
            let paywallDetected = false;
            
            if (this.currentSite === 'svd') {
                const svdPaywall = document.querySelector('[data-paywall]');
                if (svdPaywall) paywallDetected = true;
            } 
            else if (this.currentSite === 'kungalvsposten') {
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
                this.showUnlockButton();
            }
        }

        showUnlockButton() {
            if (this.button) return;

            const buttonText = this.currentSite === 'kungalvsposten' ? 'Hämta från PressReader (TEST)' : 'Hämta artikel (TEST)';
            
            this.button = document.createElement('div');
            this.button.id = 'news-unlock-button';
            this.button.innerHTML = `
                <div style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #ff6b35, #f7931e);
                    color: white;
                    padding: 12px 18px;
                    border-radius: 8px;
                    box-shadow: 0 3px 15px rgba(255,107,53,0.4);
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
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        <span>${buttonText}</span>
                    </div>
                    <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">
                        TEST MODE - Simulerade API-svar
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
            
            this.showNotification('Hämtar artikel... (SIMULERAT)', 'loading');
            
            try {
                // Simulera API-anrop med delay
                await this.simulateApiCall();
                
                const mockData = this.getMockApiResponse();
                
                if (mockData.success && mockData.result.pressreader_available) {
                    const article = mockData.result.pressreader_match.article;
                    
                    console.log(`[TEST] API Svar:`, mockData);
                    
                    if (this.currentSite === 'kungalvsposten' && article.url) {
                        this.showNotification('Öppnar artikel i PressReader... (TEST)', 'success');
                        setTimeout(() => {
                            console.log(`[TEST] Skulle öppna: ${article.url}`);
                            // I riktigt läge: window.open(article.url, '_blank');
                            this.showTestResult(article);
                        }, 1000);
                    } else {
                        this.showNotification('Artikel hittad! (TEST)', 'success');
                        setTimeout(() => {
                            this.displayArticle(mockData.result.pressreader_match);
                        }, 1000);
                    }
                } else {
                    this.showNotification('Artikeln finns inte tillgänglig (TEST)', 'error');
                }
                
            } catch (error) {
                this.showNotification('Kunde inte hämta artikel (TEST)', 'error');
            } finally {
                this.isProcessing = false;
            }
        }

        async simulateApiCall() {
            // Simulera API-delay
            return new Promise(resolve => setTimeout(resolve, 1500));
        }

        getMockApiResponse() {
            if (this.currentSite === 'svd') {
                return {
                    success: true,
                    result: {
                        pressreader_available: true,
                        pressreader_match: {
                            article: {
                                title: "Testexempel SVD-artikel",
                                subTitle: "En simulerad artikel för testning",
                                author: "Test Författare",
                                full_content: "Detta är ett simulerat artikelinnehåll för SVD. I verkligheten skulle detta vara den riktiga artikeltexten från PressReader API:et. Artikeln skulle innehålla fullständig text och all relevant information.",
                                url: "https://www.pressreader.com/article/123456789",
                                copyright: "© SVD 2025"
                            },
                            search_result: {
                                publication: {
                                    title: "Svenska Dagbladet"
                                },
                                issue: {
                                    date: "2025-01-10"
                                },
                                summary: "En kort sammanfattning av artikeln."
                            },
                            match_score: 0.95
                        }
                    }
                };
            } 
            else if (this.currentSite === 'kungalvsposten') {
                return {
                    success: true,
                    result: {
                        pressreader_available: true,
                        pressreader_match: {
                            article: {
                                title: "Bilförare stoppad – blåste positivt",
                                url: "https://www.pressreader.com/article/282475714837349"
                            },
                            search_result: {
                                publication: {
                                    title: "Kungälvs-Posten"
                                },
                                issue: {
                                    date: "08 Jul 2025"
                                }
                            },
                            match_score: 0.88
                        }
                    }
                };
            }
            
            return {
                success: false,
                result: {
                    pressreader_available: false
                }
            };
        }

        showTestResult(article) {
            const testContainer = document.createElement('div');
            testContainer.id = 'test-result-container';
            testContainer.innerHTML = `
                <div style="
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                    z-index: 10002;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 500px;
                    text-align: center;
                ">
                    <h2 style="color: #28a745; margin-bottom: 20px;">🎉 TEST FRAMGÅNGSRIK!</h2>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: left;">
                        <h3 style="margin-top: 0;">Simulerat API-svar:</h3>
                        <p><strong>Titel:</strong> ${article.title}</p>
                        <p><strong>PressReader URL:</strong> <a href="${article.url}" target="_blank">${article.url}</a></p>
                        <p><strong>Åtgärd:</strong> Skulle öppna länken i ny flik</p>
                    </div>
                    
                    <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 0; font-size: 14px; color: #1565c0;">
                            I riktigt läge skulle <code>window.open("${article.url}", "_blank")</code> köras automatiskt.
                        </p>
                    </div>
                    
                    <button onclick="this.parentElement.parentElement.remove()" style="
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                    ">Stäng test</button>
                </div>
            `;
            
            document.body.appendChild(testContainer);
        }

        showNotification(message, type) {
            const existing = document.getElementById('test-notification');
            if (existing) existing.remove();

            const notification = document.createElement('div');
            notification.id = 'test-notification';
            
            const colors = {
                loading: '#ff6b35',
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
                    ${type === 'loading' ? '<span style="margin-right: 8px;">🧪</span>' : ''}
                    ${message}
                </div>
            `;
            
            document.body.appendChild(notification);
            
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
            
            const notification = document.getElementById('test-notification');
            if (notification) notification.remove();
            
            const articleContainer = document.createElement('div');
            articleContainer.id = 'test-article-container';
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
                        background: linear-gradient(135deg, #ff6b35, #f7931e);
                        color: white;
                        padding: 15px 20px;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        z-index: 10003;
                    ">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-weight: 600;">🧪 TEST ARTIKEL HÄMTAD</span>
                        </div>
                        
                        <button id="close-test-article" style="
                            background: rgba(255,255,255,0.2);
                            border: none;
                            color: white;
                            font-size: 24px;
                            cursor: pointer;
                            padding: 5px;
                            border-radius: 4px;
                        " onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                            ×
                        </button>
                    </div>
                    
                    <div style="
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 40px 20px;
                        line-height: 1.6;
                    ">
                        <div style="
                            background: #fff3cd;
                            border: 1px solid #ffeaa7;
                            padding: 15px;
                            border-radius: 8px;
                            margin-bottom: 30px;
                            text-align: center;
                        ">
                            <strong>🧪 TEST MODE:</strong> Detta är simulerat innehåll för att testa API-integration
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
                            
                            <div>
                                <span style="font-weight: 600;">Matchning:</span>
                                <span style="color: #666;">${(matchData.match_score * 100).toFixed(0)}%</span>
                            </div>
                        </div>
                        
                        <div style="
                            font-size: 16px;
                            line-height: 1.8;
                            color: #333;
                        ">
                            ${article.full_content || searchResult.summary || 'Artikelinnehåll tillgängligt.'}
                        </div>
                        
                        <div style="
                            margin-top: 40px;
                            padding: 20px;
                            background: #e8f4fd;
                            border-radius: 8px;
                            text-align: center;
                        ">
                            <p style="margin-bottom: 15px;"><strong>🔗 PressReader Original:</strong></p>
                            <a href="${article.url}" target="_blank" style="
                                display: inline-block;
                                background: #007bff;
                                color: white;
                                padding: 12px 24px;
                                text-decoration: none;
                                border-radius: 6px;
                                font-weight: 600;
                            ">${article.url}</a>
                        </div>
                    </div>
                </div>
            `;
            
            const closeButton = articleContainer.querySelector('#close-test-article');
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
                new SwedishNewsUnlockerTest();
            });
        } else {
            new SwedishNewsUnlockerTest();
        }
    }

})();