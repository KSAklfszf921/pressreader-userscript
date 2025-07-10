# 🚀 PressReader UserScript for Swedish News

Advanced userscript that automatically detects paywalls on Swedish news sites and retrieves articles from PressReader using intelligent Boolean search strategies.

## ✨ Features

- 🎯 **Smart Paywall Detection** - Automatically detects paywalls on SVD and Kungälvsposten
- 🔍 **Advanced Boolean Search** - Multiple search strategies with AND, OR, wildcard operators
- 🔄 **Digital→Print Mapping** - Bridges gap between digital articles and PressReader's print versions
- 🎨 **Clean UI** - Elegant green button that appears for 15 seconds when paywall detected
- 🚀 **Auto-server** - Complete FastAPI backend with demo and production modes

## 🛠 Quick Start

### Option 1: One-Command Setup
```bash
git clone <your-repo-url>
cd PressReader_Extension_Latest
./start.sh
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install fastapi uvicorn python-dotenv watchdog

# Start server
python complete_server.py
```

### Option 3: GitHub Codespaces
1. Open this repo on GitHub
2. Click "Code" → "Codespaces" → "Create codespace"
3. Add your PressReader API keys as secrets
4. Everything runs automatically!

## 🔑 API Configuration

1. Get PressReader API keys from: https://developers.pressreader.com
2. Update `.env` file:
```bash
PRESSREADER_API_KEY=your_real_api_key
PRESSREADER_API_SECRET=your_real_api_secret
```
3. System automatically switches to production mode!

## 📱 Installation (UserScript)

1. Install [userscripts Safari extension](https://github.com/quoid/userscripts)
2. Copy `pressreader_userscript.js` content
3. Create new userscript in extension
4. Paste content and save

## 🧪 Demo Mode

The system includes intelligent demo mode with realistic mock data:
- ✅ Works immediately without API keys
- 🎯 Smart article matching based on site and content
- 📊 Realistic success rates and response times
- 🔄 Automatic production mode when real keys added

## 🔍 Search Strategies

The userscript uses multiple search strategies in priority order:

1. **Titel + Publikation + Datum** - `"Article Title" AND "Publication" AND "Date"`
2. **Titel + Publikation** - `"Article Title" AND "Publication"`
3. **Nyckelord + Publikation** - `(keyword1 AND keyword2) AND "Publication"`
4. **Författare + Publikation + Datum** - `"Author" AND "Publication" AND "Date"`
5. **Wildcard-sökning** - `(word1* AND word2*) AND "Publication"`
6. **URL-baserad fallback** - Last resort URL-based search

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   UserScript    │───▶│   FastAPI Server │───▶│ PressReader API │
│   (Browser)     │    │   (localhost)    │    │   (Cloud)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Files Structure

```
├── pressreader_userscript.js      # Main userscript for browser
├── complete_server.py             # FastAPI server (demo + production)
├── auto_update_api_keys.py        # Automatic API key detection
├── start.sh                       # One-command starter
├── .env                          # Configuration (API keys)
├── requirements.txt              # Python dependencies
├── .github/workflows/            # GitHub Actions
└── .devcontainer/               # Codespaces configuration
```

## 🚀 Deployment Options

### GitHub Actions (Automatic)
Push to main branch triggers automatic deployment

### GitHub Codespaces (Cloud Development)
Complete development environment in the cloud

### Local Development
Run `./start.sh` for instant local setup

## 🎯 Supported Sites

- **SVD (Svenska Dagbladet)** - Meta-tag paywall detection
- **Kungälvsposten** - Text and element-based detection
- **Easily extensible** for more Swedish news sites

## 🔧 Technical Features

- **Intelligent Paywall Detection** - Multiple detection methods per site
- **3-second delay** - Waits for page load before showing button
- **Boolean Search Optimization** - Swedish stopword filtering
- **Date Normalization** - Handles Swedish date formats
- **Publication Mapping** - Maps digital sites to print publication names

## 📊 Demo vs Production

| Feature | Demo Mode | Production Mode |
|---------|-----------|-----------------|
| API Keys | Not required | PressReader API keys required |
| Article Access | Smart mock data | Real PressReader articles |
| Success Rate | ~80% (simulated) | Depends on PressReader availability |
| Setup Time | Instant | 2 minutes (get API keys) |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add your improvements
4. Submit pull request

## 📝 License

MIT License - Feel free to use and modify!

## 🆘 Support

- Check server logs: `tail -f pressreader_api.log`
- Demo mode troubleshooting: Server runs automatically with mock data
- Production mode: Ensure API keys are valid in `.env`

---

**Made with ❤️ for Swedish journalism accessibility**