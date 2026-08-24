# 🚀 Deployment Guide - GitHub + Render.com

## Overview

This guide shows you how to deploy **Ledger Detective** using:
- **Frontend**: GitHub Pages (free, static hosting)
- **Backend**: Render.com (free tier with auto-sleep)
- **Keep-Alive**: Google Apps Script (keeps backend warm)

---

## 📋 Prerequisites

- [ ] GitHub account
- [ ] Render.com account (free)
- [ ] Google account (for Apps Script)
- [ ] Git installed locally

---

## 🔧 Part 1: Prepare the Code

### Step 1: Update Frontend for Production

Create `frontend/.env.production`:

```bash
VITE_API_URL=https://your-backend-name.onrender.com
```

Update `frontend/src/App.tsx` to use environment variable:

```typescript
// Replace hardcoded URLs with:
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Then use it in fetch calls:
await fetch(`${API_URL}/api/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question }),
})
```

### Step 2: Add Production Build Scripts

Update `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "deploy": "npm run build && gh-pages -d dist"
  },
  "devDependencies": {
    "gh-pages": "^6.0.0"
  }
}
```

Install gh-pages:

```bash
cd frontend
npm install --save-dev gh-pages
```

### Step 3: Configure Vite for GitHub Pages

Update `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/ledger-detective/', // Replace with your repo name
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## 🐙 Part 2: GitHub Setup

### Step 1: Create Repository

```bash
cd /Users/adhimulam.viswa/Documents/personal-projects/supervity/ledger-detective

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Ledger Detective"

# Create repo on GitHub (via browser), then:
git remote add origin https://github.com/YOUR_USERNAME/ledger-detective.git
git branch -M main
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** > **Pages**
3. Under **Source**, select: `gh-pages` branch
4. Save

**Your frontend will be at**: `https://YOUR_USERNAME.github.io/ledger-detective/`

---

## ☁️ Part 3: Deploy Backend to Render.com

### Step 1: Create `render.yaml`

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: ledger-detective-backend
    env: python
    region: oregon # or your preferred region
    plan: free
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: GEMINI_API_KEY
        sync: false # You'll add this manually in Render dashboard
      - key: USE_MOCK_LLM
        value: "false"
      - key: PYTHON_VERSION
        value: "3.11.0"
```

### Step 2: Deploy to Render

1. Go to [Render.com](https://render.com)
2. Sign in and click **New +** > **Web Service**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`
5. Click **Create Web Service**

**Add Environment Variables:**
- Go to your service > **Environment**
- Add `GEMINI_API_KEY` with your key
- Save

### Step 3: Get Your Backend URL

After deployment completes, you'll get a URL like:
```
https://ledger-detective-backend.onrender.com
```

**Copy this URL** - you'll need it for frontend!

---

## 🔄 Part 4: Update Frontend with Backend URL

### Step 1: Update Environment Variable

Edit `frontend/.env.production`:

```bash
VITE_API_URL=https://ledger-detective-backend.onrender.com
```

### Step 2: Rebuild and Deploy Frontend

```bash
cd frontend

# Build with production env
npm run build

# Deploy to GitHub Pages
npm run deploy
```

**Your app is now live!** 🎉

---

## ⏰ Part 5: Keep Backend Alive (Google Apps Script)

Render's free tier sleeps after 15 minutes of inactivity. Let's keep it warm!

### Step 1: Create Apps Script

1. Go to [Google Apps Script](https://script.google.com/)
2. Click **New Project**
3. Paste this code:

```javascript
function keepBackendAlive() {
  const BACKEND_URL = 'https://ledger-detective-backend.onrender.com/api/health';
  
  try {
    const response = UrlFetchApp.fetch(BACKEND_URL, {
      method: 'GET',
      muteHttpExceptions: true,
      headers: {
        'User-Agent': 'KeepAlive-Script'
      }
    });
    
    const statusCode = response.getResponseCode();
    const timestamp = new Date().toISOString();
    
    if (statusCode === 200) {
      Logger.log(`[${timestamp}] ✅ Backend is alive (${statusCode})`);
    } else {
      Logger.log(`[${timestamp}] ⚠️ Backend responded with ${statusCode}`);
    }
  } catch (error) {
    Logger.log(`[${timestamp}] ❌ Error: ${error.message}`);
  }
}

// Run this once manually to test
function testKeepAlive() {
  keepBackendAlive();
  Logger.log('Test complete. Check logs above.');
}
```

4. Save the project (name it "Ledger Detective Keep-Alive")

### Step 2: Set Up Trigger

1. Click **Triggers** (clock icon on left sidebar)
2. Click **Add Trigger**
3. Configure:
   - Choose function: `keepBackendAlive`
   - Event source: `Time-driven`
   - Type: `Minutes timer`
   - Interval: **Every 5 minutes**
4. Click **Save**

**Important**: You'll need to authorize the script first time!

### Alternative: More Advanced Keep-Alive

For better reliability, use this enhanced version:

```javascript
function keepBackendAlive() {
  const BACKEND_URL = 'https://ledger-detective-backend.onrender.com';
  const endpoints = ['/api/health', '/api/stats'];
  
  endpoints.forEach(endpoint => {
    try {
      const url = BACKEND_URL + endpoint;
      const response = UrlFetchApp.fetch(url, {
        method: 'GET',
        muteHttpExceptions: true,
        headers: {
          'User-Agent': 'KeepAlive-Script',
          'Accept': 'application/json'
        }
      });
      
      const statusCode = response.getResponseCode();
      const timestamp = new Date().toISOString();
      
      if (statusCode === 200) {
        Logger.log(`[${timestamp}] ✅ ${endpoint} -> ${statusCode}`);
      } else {
        Logger.log(`[${timestamp}] ⚠️ ${endpoint} -> ${statusCode}`);
        // Send alert email if backend is down
        if (statusCode >= 500) {
          MailApp.sendEmail({
            to: 'your-email@gmail.com',
            subject: '🚨 Ledger Detective Backend Down',
            body: `Backend returned ${statusCode} for ${endpoint} at ${timestamp}`
          });
        }
      }
    } catch (error) {
      Logger.log(`[${timestamp}] ❌ ${endpoint}: ${error.message}`);
    }
  });
}
```

---

## 📊 Part 6: Monitor Deployment

### Backend Monitoring

Check your backend status:
```bash
curl https://ledger-detective-backend.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "ai_intelligence": "active",
  "version": "2.1.0"
}
```

### Frontend Monitoring

Visit your GitHub Pages URL:
```
https://YOUR_USERNAME.github.io/ledger-detective/
```

### Apps Script Logs

1. Go to [Apps Script Dashboard](https://script.google.com/)
2. Open your project
3. Click **Executions** (left sidebar)
4. See all trigger runs and logs

---

## 🔧 Part 7: Troubleshooting

### Issue 1: Frontend Can't Connect to Backend

**Problem**: CORS error in browser console

**Fix**: Update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://YOUR_USERNAME.github.io",
        "http://localhost:3000",  # For local dev
        "http://localhost:5173"   # Vite default
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy backend.

### Issue 2: Backend Keeps Sleeping

**Problem**: Render free tier sleeps after 15 min

**Fix**: 
1. Check Apps Script is running every 5 minutes
2. Verify logs show successful pings
3. Consider upgrading to Render paid plan ($7/month for always-on)

### Issue 3: GitHub Pages Shows 404

**Problem**: Page not found

**Fix**:
1. Ensure `gh-pages` branch exists
2. Check Settings > Pages is configured correctly
3. Wait 5-10 minutes for deployment
4. Clear browser cache

### Issue 4: Database Not Persistent

**Problem**: Data resets on Render restart

**Fix**: Render's free tier doesn't persist files. Options:
1. Use Render PostgreSQL (free 90 days)
2. Use external DB (Supabase, PlanetScale free tier)
3. Keep SQLite and regenerate on startup (current approach)

---

## 📁 Part 8: Project Structure for Deployment

```
ledger-detective/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Optional: Auto-deploy on push
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env.production         # Production env vars
│   └── ...
├── src/                        # Shared backend logic
├── data/                       # CSV files
├── render.yaml                 # Render config
├── .gitignore
└── README.md
```

---

## 🤖 Part 9: Optional - GitHub Actions Auto-Deploy

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Build
        run: |
          cd frontend
          npm run build
        env:
          VITE_API_URL: ${{ secrets.BACKEND_URL }}
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/dist
```

Then add secret in GitHub:
1. Go to **Settings** > **Secrets and variables** > **Actions**
2. Add `BACKEND_URL` secret with your Render URL

---

## 💰 Cost Breakdown

### Free Tier (Current):
- **GitHub Pages**: Free (up to 100GB bandwidth/month)
- **Render.com**: Free (with sleep after 15 min inactivity)
- **Google Apps Script**: Free (up to 90 min/day runtime)
- **Total**: $0/month ✅

### Recommended Paid (Production):
- **GitHub Pages**: Still free
- **Render.com**: $7/month (always-on, no sleep)
- **Google Apps Script**: Still free
- **Total**: $7/month

---

## ✅ Final Checklist

### Before Deployment:
- [ ] Code works locally (both frontend and backend)
- [ ] Environment variables configured
- [ ] `.gitignore` includes `.env` files
- [ ] Database initializes correctly
- [ ] All dependencies listed in requirements.txt/package.json

### After Deployment:
- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] Can make queries end-to-end
- [ ] Apps Script runs every 5 minutes
- [ ] No CORS errors in browser console
- [ ] SQL queries work
- [ ] Sessions persist in browser
- [ ] Theme toggle works

---

## 🎯 URLs Summary

After deployment, you'll have:

| Service | URL |
|---------|-----|
| **Frontend** | `https://YOUR_USERNAME.github.io/ledger-detective/` |
| **Backend** | `https://ledger-detective-backend.onrender.com` |
| **API Health** | `https://ledger-detective-backend.onrender.com/api/health` |
| **API Docs** | `https://ledger-detective-backend.onrender.com/docs` |
| **Apps Script** | `https://script.google.com/home` |

---

## 📚 Additional Resources

- [Render Docs](https://render.com/docs)
- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)
- [Apps Script Docs](https://developers.google.com/apps-script)

---

## 🎉 You're Live!

Once deployed, share your live demo:
```
🚀 Ledger Detective - AI-Powered SAP Reconciliation

Live Demo: https://YOUR_USERNAME.github.io/ledger-detective/
Backend: https://ledger-detective-backend.onrender.com
GitHub: https://github.com/YOUR_USERNAME/ledger-detective

Features:
✅ Natural language to SQL
✅ Real Gemini AI integration
✅ Anomaly detection
✅ Session management
✅ Dark/Light themes
```

Good luck! 🎊
