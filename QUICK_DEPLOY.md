# 🚀 Quick Deployment Guide

## 1️⃣ Backend (Render.com) - 3 Minutes

### Option A: One-Click Deploy (Recommended)
1. Fork this repo to your GitHub
2. Go to [render.com](https://render.com)
3. Click **"New +"** → **"Blueprint"**
4. Connect your GitHub repo
5. Render will auto-detect `render.yaml`
6. Add your **GEMINI_API_KEY** in environment variables
7. Deploy! ✨

### Option B: Manual Setup
1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect GitHub repo
3. Settings:
   - **Name**: `ledger-detective-backend`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11
4. Add Environment Variables:
   - `GEMINI_API_KEY` = your key
   - `USE_MOCK_LLM` = false
5. Deploy!

**Your backend URL**: `https://ledger-detective-backend.onrender.com`

---

## 2️⃣ Frontend (GitHub Pages) - 2 Minutes

### Setup
```bash
cd frontend
npm install
```

### Configure API URL
Edit `frontend/.env.production`:
```bash
VITE_API_URL=https://your-backend-name.onrender.com
```

### Deploy
```bash
npm run deploy
```

**Your app**: `https://yourusername.github.io/ledger-detective/`

---

## 3️⃣ Keep Backend Alive (Google Apps Script)

### Why?
Render.com free tier sleeps after 15 minutes of inactivity. This script pings it every 10 minutes.

### Setup (2 minutes)
1. Go to [script.google.com](https://script.google.com)
2. Create new project
3. Paste this code:

```javascript
function keepAlive() {
  const url = 'https://your-backend-name.onrender.com/api/health';
  
  try {
    const response = UrlFetchApp.fetch(url, {
      method: 'get',
      muteHttpExceptions: true
    });
    
    const timestamp = new Date().toLocaleString();
    
    if (response.getResponseCode() === 200) {
      Logger.log(`[${timestamp}] ✅ Backend is alive`);
    } else {
      Logger.log(`[${timestamp}] ⚠️ Got status ${response.getResponseCode()}`);
    }
  } catch (error) {
    Logger.log(`[${timestamp}] ❌ Error: ${error.message}`);
  }
}

// Optional: Setup email alerts
function setupAlerts() {
  const email = 'your-email@gmail.com';
  const url = 'https://your-backend-name.onrender.com/api/health';
  
  try {
    const response = UrlFetchApp.fetch(url, {
      method: 'get',
      muteHttpExceptions: true
    });
    
    if (response.getResponseCode() !== 200) {
      MailApp.sendEmail({
        to: email,
        subject: '⚠️ Ledger Detective Backend Down',
        body: `Backend returned status: ${response.getResponseCode()}`
      });
    }
  } catch (error) {
    MailApp.sendEmail({
      to: email,
      subject: '❌ Ledger Detective Backend Error',
      body: `Error: ${error.message}`
    });
  }
}
```

4. **Set Trigger**:
   - Click ⏰ (Triggers) in left sidebar
   - Add Trigger
   - Function: `keepAlive`
   - Event: Time-driven, Minutes timer, Every 10 minutes
   - Save

---

## 🎉 Done!

**Test your app**: Open `https://yourusername.github.io/ledger-detective/`

### Troubleshooting

**Backend not responding?**
- Check Render.com logs
- Verify GEMINI_API_KEY is set
- Try manual wake: `curl https://your-backend.onrender.com/api/health`

**Frontend can't connect?**
- Check `frontend/.env.production` has correct URL
- Rebuild: `npm run build && npm run deploy`
- Check browser console for CORS errors

**CORS errors?**
- Update `backend/main.py` → `allow_origins` to include your GitHub Pages URL

---

## 📊 Expected Costs

| Service | Plan | Cost |
|---------|------|------|
| Render.com | Free Tier | $0/month |
| GitHub Pages | Free | $0/month |
| Google Apps Script | Free | $0/month |
| **Total** | | **$0/month** |

**Note**: Render free tier sleeps after 15 min inactivity. First request takes ~30 seconds to wake. Use the Google Apps Script to keep it warm.

---

## 🔧 Custom Domain (Optional)

### Backend
1. Render.com → Service → Settings → Custom Domain
2. Add your domain (e.g., `api.yourdomain.com`)

### Frontend
1. Add `CNAME` file in `frontend/public/`:
   ```
   yourdomain.com
   ```
2. GitHub repo → Settings → Pages → Custom domain
3. Update DNS: `CNAME` record → `yourusername.github.io`

---

Need help? Check the full [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
