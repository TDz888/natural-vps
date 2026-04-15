# Natural VPS - Quick Start Guide v3.0

## 🚀 Installation & Deployment

### Prerequisites
- Python 3.8+
- pip or conda
- SQLite3
- 2GB RAM minimum

### Installation Steps

#### 1. Clone/Extract Repository
```bash
cd natural-vps-main
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment (Optional)
Create `.env` file (optional, uses defaults):
```
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5000
JWT_EXPIRE_HOURS=24
DB_PATH=data/vps.db
```

#### 4. Initialize Database
Database auto-initializes on first run:
```bash
python run.py
```

Server will start at: **http://localhost:5000**

---

## 📊 Admin Panel Access

### Access the Admin Dashboard
1. Navigate to: `http://localhost:5000/admin`
2. Login with credentials:
   - **Username:** `superdzan`
   - **Password:** `ThienAn_88`

### Admin Features
- 📈 Real-time dashboard stats
- 👥 User management
- 🖥️ VM monitoring
- 🚫 Anti-spam controls
- ⚠️ Threat detection
- 📋 System logs
- ⚙️ Configuration view

---

## 🔐 User Registration & Authentication

### User Registration Flow
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Registration successful",
  "user": {
    "id": "uuid...",
    "username": "john_doe",
    "api_key": "nv_..."
  }
}
```

### Email Verification (If Required)
```bash
# Request Code
POST /api/auth/request-verification-code
{"email": "john@example.com"}

# Verify Code
POST /api/auth/verify-email
{
  "email": "john@example.com",
  "code": "123456"
}
```

### User Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

---

## 🖥️ VM Management

### Create Virtual Machine
```bash
POST /api/vps
Authorization: Bearer {token}
Content-Type: application/json

{
  "githubToken": "ghp_...",
  "tailscaleKey": "tskey_...",
  "osType": "ubuntu",
  "vmUsername": "admin",
  "vmPassword": "SecurePass123!"
}
```

### List User VMs
```bash
GET /api/vps
Authorization: Bearer {token}
```

### Get VM Progress
```bash
GET /api/vps/{vm_id}/progress
Authorization: Bearer {token}
```

---

## 🛡️ Anti-Spam Features

### Registration Protection
- **Limit:** 3 registrations per IP per hour
- **Limit:** 10 registrations per IP per day
- **Protection:** Blocks disposable emails

### VM Creation Protection
- **Limit:** 5 VMs per user per hour
- **Limit:** 15 VMs per user per day
- **Limit:** 10 VMs per IP per hour

### Login Protection
- **Limit:** 10 failed attempts per IP per hour
- **Limit:** 5 failed attempts per user per hour
- **Action:** Auto-blocks after threshold

---

## 📧 Email System

### Supported Email Validation
✅ Standard domain emails
✅ Complex local parts (name+tag)
✅ International domains

❌ Blocked Services:
- tempmail.io, tempmail.com
- 10minutemail.com, mailinator.com
- throwaway.email, guerrillamail.com
- And 7+ more

---

## 🔑 API Key Management

### Get User Info
```bash
GET /api/auth/me
Authorization: Bearer {token}

Response:
{
  "success": true,
  "user": {
    "id": "...",
    "username": "...",
    "email": "...",
    "api_key": "nv_...",
    "created_at": "2025-01-15T10:30:00"
  }
}
```

### API Key Usage
```bash
# Use in header
Authorization: Bearer {api_key}

# Or as parameter
?api_key={api_key}
```

---

## 📊 Admin API Endpoints

### Admin Login
```bash
POST /api/admin/login
{
  "username": "superdzan",
  "password": "ThienAn_88"
}

Response:
{
  "success": true,
  "token": "admin_jwt_token",
  "message": "Admin login successful"
}
```

### Dashboard Stats
```bash
GET /api/admin/dashboard
Authorization: Bearer {admin_token}

Response:
{
  "success": true,
  "stats": {
    "total_users": 42,
    "active_users": 38,
    "running_vms": 105,
    "blocked_ips": 7,
    "failed_logins_24h": 23,
    "new_registrations_24h": 5
  }
}
```

### User Management
```bash
GET /api/admin/users
Authorization: Bearer {admin_token}

POST /api/admin/user/{user_id}/suspend
Authorization: Bearer {admin_token}

POST /api/admin/user/{user_id}/unsuspend
Authorization: Bearer {admin_token}
```

### Spam Statistics
```bash
GET /api/admin/spam-stats
Authorization: Bearer {admin_token}
```

### Active Threats
```bash
GET /api/admin/threats
Authorization: Bearer {admin_token}
```

### System Logs
```bash
GET /api/admin/logs?type=api
GET /api/admin/logs?type=admin
GET /api/admin/logs?type=system
Authorization: Bearer {admin_token}
```

---

## 🧪 Testing

### Run Anti-Spam Tests
```bash
python test_antispam.py
```

**Expected Output:**
```
✅ Testing Email Validation... ✓
✅ Testing Email Code Generation... ✓
✅ Testing Email Code Verification... ✓
✅ Testing Registration Spam Detection... ✓
✅ Testing Login Spam Detection... ✓
✅ Testing IP Reputation... ✓
✅ Testing User Spam Score... ✓
✅ Testing Email Reputation... ✓

✓ ALL TESTS PASSED!
```

---

## 📋 Monitoring & Logs

### Log Files
- `app.log` - Application events
- `errors.log` - Error tracking
- `security.log` - Security events

### Check System Health
```bash
GET /api/health
```

### Monitor Requests
```bash
GET /api/monitor/dashboard
Authorization: Bearer {token}
```

---

## 🔧 Configuration

### Rate Limit Settings
Edit `app/config.py`:
```python
RATE_LIMIT_WINDOW = 10800  # 3 hours
RATE_LIMIT_COUNT = 5       # 5 VMs per window
```

### Email Verification
Edit `app/email_verification.py`:
```python
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY_MINUTES = 15
MAX_ATTEMPTS = 3
```

### Spam Detection Thresholds
Edit `app/spam_detector.py`:
```python
REGISTRATION_LIMITS = {
    'per_ip_per_hour': 3,
    'per_ip_per_day': 10,
}
```

---

## 🆘 Troubleshooting

### Database Error: "No such table"
**Solution:** Delete `data/vps.db` and restart
```bash
rm data/vps.db
python run.py
```

### "Too many login attempts"
**Solution:** Wait 1 hour or admin clears IP blacklist

### Email verification not sending
**Solution:** Email service not configured (implement SendGrid/AWS SES)

### Admin panel not loading
**Solution:** Check `/admin` route, ensure admin.html in templates/

### CORS errors
**Solution:** Ensure `credentials: 'include'` in fetch calls

---

## 🚀 Deployment to Production

### Pre-Deployment Checklist
- [ ] Change admin password
- [ ] Set proper SECRET_KEY
- [ ] Configure email service (SendGrid/AWS)
- [ ] Update CORS origins
- [ ] Enable HTTPS/SSL
- [ ] Set appropriate rate limits
- [ ] Configure database backup
- [ ] Set up monitoring

### Docker Deployment (Optional)
```bash
python -m pytest  # Run all tests
python run.py     # Start server
```

### Systemd Service (Linux)
Create `/etc/systemd/system/natural-vps.service`:
```ini
[Unit]
Description=Natural VPS
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/natural-vps
ExecStart=/usr/bin/python3 run.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 📞 Support

### Documentation
- `IMPLEMENTATION_REPORT.md` - Full technical report
- `ANTISPAM_GUIDE.md` - Anti-spam system guide
- `PRODUCTION.md` - Production features guide

### Contact
- Email: thienantran1268@gmail.com
- Admin: superdzan

### Common Issues
Check logs for detailed error messages:
```bash
tail -f app.log        # Real-time logs
grep ERROR errors.log  # Error summary
```

---

## 📝 Version Info

**Current Version:** 3.0.0
**Release Date:** January 2025
**Status:** Production Ready ✅

### What's New in v3.0
- ✅ Advanced email verification
- ✅ Professional anti-spam system
- ✅ Enterprise admin panel
- ✅ User management
- ✅ Threat detection
- ✅ Complete documentation

---

**Ready to deploy? Start the server with:**
```bash
python run.py
```

**🎉 Welcome to Natural VPS v3.0!**
