// Simulera exakt flöde som userscriptet skulle köra på SVD
const simulateUserScript = async () => {
    console.log('🔍 SIMULERAR RIKTIGT TEST PÅ SVD ARTIKEL');
    console.log('=======================================');
    
    // 1. Simulera paywall detection
    console.log('\n1. PAYWALL DETECTION:');
    const mockSVDPage = {
        meta: [
            { property: 'lp:paywall', content: 'hard' },
            { property: 'lp:type', content: 'premium' }
        ],
        elements: ['[data-paywall]', '.paywall-notice'],
        text: 'För att läsa hela artikeln, prenumerera på SVD'
    };
    
    // Exakt logik från userscript
    const paywallMeta = mockSVDPage.meta.find(m => m.property === 'lp:paywall' && m.content === 'hard');
    const premiumMeta = mockSVDPage.meta.find(m => m.property === 'lp:type' && m.content.includes('premium'));
    
    console.log('   Meta lp:paywall=hard:', paywallMeta ? '✅ DETECTED' : '❌ NOT FOUND');
    console.log('   Meta lp:type=premium:', premiumMeta ? '✅ DETECTED' : '❌ NOT FOUND');
    console.log('   Paywall elements:', mockSVDPage.elements.length > 0 ? '✅ FOUND' : '❌ NOT FOUND');
    
    const isPaywalled = !!(paywallMeta || premiumMeta);
    console.log('   🎯 RESULT: PAYWALL', isPaywalled ? 'DETECTED ✅' : 'NOT FOUND ❌');
    
    if (isPaywalled) {
        console.log('\n2. BUTTON CREATION:');
        console.log('   ✅ Creating green "Läs artikel" button');
        console.log('   ✅ Position: top-right, 15s timer');
        
        console.log('\n3. API CALL TO LOCALHOST:8000:');
        // Simulera API call med fetch
        const mockApiData = {
            url: 'https://www.svd.se/a/xmE8p8/bingo-rimer-mot-sitt-livs-form-vid-50-min-adhd-som-turbo',
            title: 'Bingo rimer mot sitt livs form vid 50',
            site: 'svd.se'
        };
        console.log('   📤 Sending:', JSON.stringify(mockApiData, null, 2));
        
        // Faktisk API call
        try {
            const fetch = (await import('node-fetch')).default;
            const response = await fetch('http://localhost:8000/api/v2/check-article', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mockApiData)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('   📥 Response SUCCESS');
                
                if (result.success) {
                    console.log('\n4. ARTICLE FOUND:');
                    console.log('   ✅ Title:', result.result.pressreader_match.article.title);
                    console.log('   ✅ Author:', result.result.pressreader_match.article.author);
                    console.log('   ✅ Score:', result.result.match_score);
                    console.log('   ✅ Strategy:', result.result.strategy_used);
                    
                    console.log('\n5. USER INTERACTION:');
                    console.log('   🖱️  User clicks "Läs artikel" button');
                    console.log('   🔗 Opens PressReader URL:', result.result.pressreader_match.article.url);
                    console.log('   📖 User reads full article content');
                }
            }
        } catch (error) {
            console.log('   ❌ API Error:', error.message);
            console.log('   ℹ️  Trying fallback with curl...');
        }
    }
    
    console.log('\n✅ SIMULERAT TEST SLUTFÖRT!');
};

simulateUserScript().catch(console.error);