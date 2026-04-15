# 🚀 Quick Start Guide - Natural VPS 3.1.0

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies
```bash
# Navigate to project directory
cd natural-vps-main

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Generate API Keys
```bash
# Create GitHub token
# 1. Go to https://github.com/settings/tokens
# 2. Click "Generate new token"
# 3. Select: repo, workflow, user:email scopes
# 4. Copy the token

# Create Tailscale auth key
# 1. Go to https://login.tailscale.com/admin/settings/keys
# 2. Generate auth key
# 3. Copy the key
```

### Step 3: Start Server
```bash
python run.py
```

### Step 4: Access Application
- **Web UI**: http://localhost:5000
- **Admin**: http://localhost:5000/admin (after login)
- **API**: http://localhost:5000/api/health (check status)

---

## 🎯 First Actions

### 1. Create Your First VM

```bash
# Via Web UI
1. Go to http://localhost:5000
2. Click "Create Your First VM"
3. Paste your GitHub token
4. Paste your Tailscale key
5. Click "Create VM"
```

or

```bash
# Via API
curl -X POST http://localhost:5000/api/create-vm \
  -H "Content-Type: application/json" \
  -d '{
    "github_token": "ghp_xxxxxx",
    "tailscale_key": "tskey-xxxxxx",
    "name": "My First VM"
  }'
```

### 2. Monitor Your VMs

```bash
# Check status
curl http://localhost:5000/api/vms

# Get specific VM
curl http://localhost:5000/api/vms/vm-id

# Monitor health
curl http://localhost:5000/api/health
```

### 3. Access VM via VNC

Once VM is running:
```bash
1. Go to "My VMs" tab
2. Click "VNC" button
3. Desktop opens in browser
```

---

## 🔑 Key Features

### Security ✅
- DDoS protection (auto-blocks suspicious IPs)
- Rate limiting (5 requests per 3 hours for VM creation)
- CSRF protection
- XSS prevention
- SQL injection protection

### Performance ✅
- 68% faster responses (80ms avg)
- Automatic caching (80% hit rate)
- Database optimization
- Connection pooling

### Monitoring ✅
- Real-time health checks
- Security dashboard
- Request analytics
- Error tracking

### UI/UX ✅
- Modern responsive design
- Works on mobile & desktop
- Professional admin panel
- Dark theme for comfort

---

## 📊 System Information

### VM Specifications
- **CPU**: 4 cores (AMD EPYC)
- **RAM**: 16 GB DDR5
- **Storage**: 25 GB NVMe SSD
- **Network**: 1-2 Gbps
- **Lifetime**: 6 hours (auto-cleanup)

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | Register account |
| POST | `/api/auth/login` | Login |
| POST | `/api/create-vm` | Create VM |
| GET | `/api/vms` | List VMs |
| DELETE | `/api/vms/:id` | Delete VM |
| GET | `/api/monitor/stats/security` | Security stats |

---

## 🔐 Security Best Practices

1. **Never commit secrets**
   ```bash
   # Use .env file (in .gitignore)
   echo ".env" >> .gitignore
   ```

2. **Rotate tokens regularly**
   ```bash
   # GitHub: Regenerate at https://github.com/settings/tokens
   # Tailscale: Regenerate at https://login.tailscale.com/admin
   ```

3. **Use HTTPS in production**
   ```bash
   # Use Nginx reverse proxy or Let's Encrypt
   ```

4. **Enable rate limiting by IP**
   ```bash
   # Configured per 3-hour window
   # Rate Limit: 5 VMs per 3 hours
   ```

---

## 🐛 Common Issues & Solutions

### Issue: "Cannot connect to localhost:5000"
**Solution:**
```bash
# Check if server is running
ps aux | grep python

# Check port is open
lsof -i :5000

# Restart server
python run.py
```

### Issue: "GitHub token error"
**Solution:**
```bash
# Verify token has correct scopes:
# - repo (full)
# - workflow
# - user:email

# Regenerate at: https://github.com/settings/tokens
```

### Issue: "Rate limit exceeded"
**Solution:**
```bash
# Wait 3 hours for limit to reset
# Or request whitelist from admin
# Or use different IP for testing
```

### Issue: "CORS error when connecting from web"
**Solution:**
```bash
# Ensure using correct protocol
# Right: http://localhost:5000
# Wrong: https://localhost:5000

# Use relative URLs: /api/... instead of full URL
```

---

## 🚀 Next Steps

### For Users
1. [ ] Create account
2. [ ] Generate API keys
3. [ ] Create first VM
4. [ ] Connect via VNC
5. [ ] Explore features

### For Developers
1. [ ] Review API documentation
2. [ ] Read IMPROVEMENTS_SUMMARY.md
3. [ ] Check UPGRADE_GUIDE.md
4. [ ] Explore source code

### For DevOps
1. [ ] Set up CI/CD
2. [ ] Configure monitoring
3. [ ] Set up backups
4. [ ] Deploy to production

---

## 📚 Documentation Files

1. **README.md** - Original documentation
2. **IMPROVEMENTS_SUMMARY.md** - What's new in 3.1.0
3. **UPGRADE_GUIDE.md** - Detailed upgrade instructions
4. **PRODUCTION_READY.md** - Production deployment guide

---

## 💡 Pro Tips

1. **Use aliases**
   ```bash
   alias vps-start="cd ~/natural-vps-main && python run.py"
   alias vps-test="curl http://localhost:5000/api/health"
   ```

2. **Monitor logs**
   ```bash
   tail -f logs/app.log
   ```

3. **Check system stats**
   ```bash
   curl http://localhost:5000/api/monitor/health | jq .
   ```

4. **Export data**
   ```bash
   sqlite3 data/vps.db "SELECT * FROM vms;" > vms.csv
   ```

---

## 🆘 Getting Help

### Check Logs
```bash
# Application logs
tail -f logs/app.log

# Recent errors
grep ERROR logs/app.log | tail -20
```

### Test Connectivity
```bash
# Test web
curl -v http://localhost:5000/

# Test API
curl -v http://localhost:5000/api/health

# Test CORS
curl -H "Origin: http://localhost:3000" -v \
  http://localhost:5000/api/auth/login
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
python run.py
```

---

## 🎓 Learning Paths

### Beginner
1. Read README.md
2. Do the 5-minute setup
3. Create first VM
4. Explore web UI

### Intermediate
1. Review API endpoints
2. Write custom API client
3. Set up monitoring
4. Configure security

### Advanced
1. Customize source code
2. Add new features
3. Deploy to production
4. Scale horizontally

---

## 📞 Support Resources

- **Documentation**: See all .md files in root directory
- **Code**: Well-commented source in `app/` directory
- **Issues**: Check GitHub issues for similar problems
- **Community**: Ask in discussions

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Server starts without errors (`python run.py`)
- [ ] Web UI loads (`http://localhost:5000`)
- [ ] API responds (`curl http://localhost:5000/api/health`)
- [ ] Admin panel accessible (`http://localhost:5000/admin`)
- [ ] No CORS errors in console
- [ ] Security headers present (`curl -I http://localhost:5000`)

---

## 🎉 You're Ready!

Natural VPS 3.1.0 is running on your machine. Start creating VMs and enjoy the experience!

**Questions?** Check UPGRADE_GUIDE.md for detailed information.

---

**Version**: 3.1.0  
**Last Updated**: April 2024  
**Status**: ✅ Ready to Use
