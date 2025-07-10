// ==UserScript==
// @name            Swedish News Unlocker
// @version         3.1.0
// @description     Unlock Swedish news articles through PressReader
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

    // Global configuration
    const CONFIG = {
        API_URL: 'http://localhost:8000/api/v2',
        BUTTON_DELAY: 2000, // 2 seconds delay before showing button
        BUTTON_TIMEOUT: 15000, // Hide button after 15 seconds
        DEBUG: true
    };

    function log(message, data = null) {
        if (CONFIG.DEBUG) {
            console.log(`[News Unlocker] ${message}`, data || '');
        }
    }

    class NewsUnlocker {
        constructor() {
            this.currentSite = this.detectSite();
            this.button = null;
            this.isProcessing = false;
            
            log(`Initialized on ${this.currentSite}`);
            this.init();
        }

        detectSite() {
            const hostname = window.location.hostname;
            if (hostname.includes('svd.se')) return 'svd';
            if (hostname.includes('kungalvsposten.se')) return 'kungalvsposten';
            return 'unknown';
        }

        init() {
            // Wait for page to load, then check for paywall
            setTimeout(() => {
                this.checkForPaywall();
            }, 1000);
        }

        checkForPaywall() {
            log('Checking for paywall...');
            let paywallDetected = false;

            if (this.currentSite === 'svd') {
                // SVD paywall detection
                const paywallMeta = document.querySelector('meta[property="lp:paywall"]');
                const premiumMeta = document.querySelector('meta[property="lp:type"]');
                const pageText = document.body.innerText.toLowerCase();
                
                const paywallTexts = [
                    'för att läsa hela artikeln',
                    'logga in för att läsa',
                    'prenumerera',
                    'premium'
                ];
                
                const hasPaywallText = paywallTexts.some(text => pageText.includes(text));
                
                if (paywallMeta || premiumMeta || hasPaywallText) {
                    paywallDetected = true;
                    log('SVD paywall detected', { paywallMeta: !!paywallMeta, premiumMeta: !!premiumMeta, hasPaywallText });
                }
            } 
            else if (this.currentSite === 'kungalvsposten') {
                // Kungälvsposten paywall detection
                const pageText = document.body.innerText.toLowerCase();
                const hasPaywallText = pageText.includes('prenumeration') || 
                                     pageText.includes('logga in') ||
                                     pageText.includes('paywall');
                
                if (hasPaywallText) {
                    paywallDetected = true;
                    log('Kungälvsposten paywall detected');
                }
            }

            if (paywallDetected) {
                log('Paywall detected, showing button after delay...');
                setTimeout(() => {
                    this.showUnlockButton();
                }, CONFIG.BUTTON_DELAY);
            } else {
                log('No paywall detected');
            }
        }

        showUnlockButton() {
            if (this.button) return; // Button already shown

            log('Showing unlock button');
            
            this.button = document.createElement('div');
            this.button.innerHTML = `
                <div id="news-unlock-btn" style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #28a745, #20692e);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(40,167,69,0.4);
                    cursor: pointer;
                    z-index: 10000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-size: 14px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    border: none;
                    min-width: 200px;
                    text-align: center;
                    animation: slideIn 0.5s ease-out;
                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    📰 Läs artikel i PressReader
                </div>
                <style>
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                </style>
            `;

            this.button.querySelector('#news-unlock-btn').addEventListener('click', () => {
                this.unlockArticle();
            });

            document.body.appendChild(this.button);

            // Auto-hide after timeout
            setTimeout(() => {
                this.hideButton();
            }, CONFIG.BUTTON_TIMEOUT);
        }

        async unlockArticle() {
            if (this.isProcessing) return;
            
            this.isProcessing = true;
            this.hideButton();
            this.showNotification('Hämtar artikel från PressReader...', 'loading');

            try {
                // Extract article data
                const articleData = this.extractArticleData();
                log('Extracted article data:', articleData);

                // Call API
                const response = await fetch(`${CONFIG.API_URL}/check-article`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(articleData)
                });

                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }

                const data = await response.json();
                log('API response:', data);

                if (data.success && data.result && data.result.pressreader_match) {
                    const article = data.result.pressreader_match.article;
                    
                    this.showNotification('Artikel hittad! Öppnar PressReader...', 'success');
                    
                    setTimeout(() => {
                        if (article.url) {
                            log('Opening PressReader URL:', article.url);
                            window.open(article.url, '_blank');
                        } else {
                            this.showNotification('Artikel saknar URL', 'error');
                        }
                    }, 1000);
                } else {
                    this.showNotification('Artikeln hittades inte i PressReader', 'error');
                }

            } catch (error) {
                log('Error:', error);
                this.showNotification('Fel vid hämtning av artikel', 'error');
            } finally {
                this.isProcessing = false;
            }
        }

        extractArticleData() {
            // Extract title
            let title = '';
            const titleSelectors = ['h1', '[property="og:title"]', 'title'];
            for (const selector of titleSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    title = (element.textContent || element.content || '').trim();
                    if (title.length > 5) break;
                }
            }

            // Extract author
            let author = '';
            const authorSelectors = ['[class*="author"]', '[class*="byline"]', '[rel="author"]'];
            for (const selector of authorSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    author = element.textContent.trim();
                    if (author.length > 2) break;
                }
            }

            return {
                url: window.location.href,
                title: title,
                author: author,
                site: this.currentSite
            };
        }

        showNotification(message, type) {
            // Remove existing notification
            const existing = document.getElementById('news-notification');
            if (existing) existing.remove();

            const colors = {
                loading: '#007bff',
                success: '#28a745',
                error: '#dc3545'
            };

            const notification = document.createElement('div');
            notification.id = 'news-notification';
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
                    max-width: 300px;
                ">
                    ${type === 'loading' ? '⏳ ' : ''}${message}
                </div>
            `;

            document.body.appendChild(notification);

            // Auto-hide (except for loading)
            if (type !== 'loading') {
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 4000);
            }
        }

        hideButton() {
            if (this.button) {
                this.button.style.opacity = '0';
                this.button.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (this.button) {
                        this.button.remove();
                        this.button = null;
                    }
                }, 300);
            }
        }
    }

    // Initialize only on supported sites
    const hostname = window.location.hostname;
    if (hostname.includes('svd.se') || hostname.includes('kungalvsposten.se')) {
        log('Initializing News Unlocker...');
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                new NewsUnlocker();
            });
        } else {
            new NewsUnlocker();
        }
    }

})();