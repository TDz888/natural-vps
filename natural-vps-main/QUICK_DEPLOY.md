# 🚀 Natural VPS v4.0.0 - Quick Start

## Installation (5 minutes)

### 1. Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment
Create `.env` or copy `.env.example`:
```bash
PORT=5000
DEBUG=false
SECRET_KEY=your-very-secret-key-here-min-32-chars
JWT_SECRET=your-jwt-secret-key-here-min-32-chars
ENABLE_KAMI=true
```

### 3. Start Server
```bash
python run.py
```

You should see:
```
🚀 Starting Natural VPS server on 0.0.0.0:5000
```

---

## Access Points

| URL | Purpose |
|-----|---------|
| `http://localhost:5000` | Auth page (register/login) |
| `http://localhost:5000/dashboard` | User dashboard |
| `http://localhost:5000/admin` | Admin panel |
| `http://localhost:5000/api/health` | API status |

---

## User Registration

1. **Go to** `http://localhost:5000`
2. **Click** "Create Account" tab
3. **Enter** your REAL email (Gmail, Outlook, etc.)
4. **System generates**:
   - Username: `swift_eagle123` ✅
   - Password: `SaF3P@ssw0rd!` ✅
   - VPS Email: `nv_abc12def34@naturalvps` ✅
5. **Directed to dashboard** 🎉

---

## Login

Use either:
- Username: `swift_eagle123`
- Email: `nv_abc12def34@naturalvps`

Password: (your generated password)

---

## Create Your First VM

1. In dashboard, click **"Create New"** tab
2. Fill in:
   - VM Name: `my-dev-server`
   - OS: Ubuntu 22.04
   - GitHub Token: `ghp_xxxxxxxxxxxx`
   - Tailscale Key: `tskey-xxxxxxxxxxxx`
3. Click **"Create VM"** 🚀
4. Wait 2-3 minutes for setup

You'll get:
- SSH command
- VNC URL
- Kami public tunnel URL
- Tailscale IP

---

## Features Ready Now ✅

- [x] Beautiful auth page
- [x] Auto-generated credentials
- [x] User dashboard
- [x] VM management
- [x] Admin panel
- [x] Kami tunnel auto-setup
- [x] Notification system (database)
- [x] Activity logging

---

## Coming Soon 🔄

- [ ] Email sending
- [ ] Notification UI
- [ ] 2FA setup
- [ ] WebSocket real-time updates
- [ ] Cost analytics
- [ ] Advanced scheduling

---

## Need Help?

Check `IMPLEMENTATION_V4.md` for complete documentation

---

**Ready to deploy?** 🌿
