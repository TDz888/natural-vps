
<div align="center">
  <img src="https://images.pexels.com/photos/957024/forest-trees-perspective-bare-trees-957024.jpg" alt="Natural VPS Banner" width="100%" style="border-radius: 20px; opacity: 0.8;" />
  
  # 🌿 NATURAL VPS
  
  *Cinematic Nature 4K • Sustainable Computing*
  
  [![Version](https://img.shields.io/badge/version-2.1.0-6b8e4e?style=for-the-badge)](https://github.com/TDz888/natural-vps)
  [![Python](https://img.shields.io/badge/Python-3.11-4a7c59?style=for-the-badge&logo=python)](https://python.org)
  [![Flask](https://img.shields.io/badge/Flask-3.0-2d5a3f?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
  [![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://docker.com)
  [![License](https://img.shields.io/badge/License-MIT-8fbc6a?style=for-the-badge)](LICENSE)

  <br/>
  
  <p align="center">
    <i>Where technology meets tranquility.</i><br/>
    <i>Deploy virtual machines as naturally as trees grow.</i>
  </p>

  <br/>
  
  <table align="center">
    <tr>
      <td align="center"><b>🌱 4 vCore</b><br/>AMD EPYC™</td>
      <td align="center"><b>💧 16GB RAM</b><br/>DDR5</td>
      <td align="center"><b>🌳 25GB SSD</b><br/>NVMe</td>
      <td align="center"><b>🌊 1-2 Gbps</b><br/>Network</td>
    </tr>
  </table>
</div>

---

## 🌲 About The Project

Natural VPS is a beautiful, cinematic VPS management platform that combines the power of GitHub Actions with the serenity of nature. Create and manage virtual machines through an intuitive interface inspired by forests, rivers, and the tranquility of the natural world.

> *"Just as a forest grows one tree at a time, your virtual infrastructure grows one VM at a time."*

### ✨ Why Natural VPS?

| Feature | Description |
|---------|-------------|
| 🎬 **Cinematic Experience** | Immersive 4K nature backgrounds with smooth animations |
| 🔐 **Secure by Design** | JWT authentication, bcrypt passwords, rate limiting |
| ⚡ **High Performance** | Connection pooling, SQLite WAL mode, Redis caching |
| 🖥️ **Multi-OS Support** | Ubuntu 22.04 LTS and Windows Server 2022 |
| 🌐 **Global Access** | Tailscale VPN + Cloudflare Tunnel integration |
| 📦 **Docker Ready** | One-command deployment with Docker Compose |
| 🎨 **Fully Responsive** | Beautiful on desktop, tablet, and mobile |

---

## 📚 User Guide

### 🌱 Getting Started

#### 1. Register an Account
Visit the application URL and click the **Register** tab. Fill in your desired username, email (optional), and a strong password.

#### 2. Prepare Your Credentials
Before creating a VM, you need two keys:

- **GitHub Personal Access Token**: 
  1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
  2. Click **Generate new token (classic)**
  3. Select scopes: `repo` and `workflow`
  4. Copy the generated token (starts with `ghp_`)

- **Tailscale Auth Key**:
  1. Go to [Tailscale Admin > Keys](https://login.tailscale.com/admin/settings/keys)
  2. Click **Generate auth key**
  3. Copy the key (starts with `tskey-auth-`)

#### 3. Create Your First VM
1. Log in to Natural VPS
2. Paste your **GitHub Token** and **Tailscale Key**
3. Choose your operating system (Ubuntu or Windows)
4. Enter a username and password for the VM (or click **Generate**)
5. Click **Grow New VM**

The VM will begin provisioning. After 15-30 seconds, it will appear in your **Virtual Forest** list.

### 🌿 Managing Your VMs

| Action | How To |
|--------|--------|
| **View VM Details** | Click on any VM in the list to expand details |
| **Copy SSH Command** | Click the copy button next to SSH (Ubuntu only) |
| **Open VNC Console** | Click the external link icon (Windows/Cloudflare) |
| **Delete VM** | Click the trash icon and confirm |

### 🍃 Connecting to Your VM

#### Ubuntu (SSH)
```bash
# Copy the SSH command from VM details and paste in terminal
ssh username@100.x.x.x
# Enter the password when prompted


Windows (Remote Desktop)

1. Open Remote Desktop Connection on Windows
2. Enter the Tailscale IP address
3. Enter your VM username and password

Via Web Browser (noVNC)

Click the Cloudflare URL link to access your VM's desktop directly in your browser.

🌳 Tips & Best Practices

· 🔐 Never share your GitHub Token or Tailscale Key
· ⏰ VMs automatically expire after 6 hours
· 📊 Monitor your usage in the stats cards
· 🔄 Use the refresh button to sync VM status
· 🌙 The interface is designed for long, comfortable sessions

---

🛠️ Tech Stack

Category Technology Purpose
Backend Flask 3.0 Web framework
Database SQLite + WAL Data persistence
Cache Redis (optional) Performance
Auth JWT + bcrypt Security
Server Gunicorn Production WSGI
Frontend HTML5/CSS3/JS User interface
Icons Font Awesome 6 Visual elements
Fonts Cormorant Garamond Elegant typography
Container Docker + Compose Deployment

---

🚀 Getting Started (Installation)

Prerequisites

· GitHub Account with a Personal Access Token
· Tailscale Account with an Auth Key
· Docker (recommended) or Python 3.11+

🐳 Docker Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/TDz888/natural-vps.git
cd natural-vps

# Copy environment file
cp .env.example .env

# Edit .env with your secrets
nano .env

# Start the application
docker-compose up -d --build
```

Visit http://localhost:5000 and start growing your virtual forest!

🐍 Manual Installation

```bash
# Clone the repository
git clone https://github.com/TDz888/natural-vps.git
cd natural-vps

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your secrets
nano .env

# Run the application
python run.py
```

---

⚙️ Configuration

Create a .env file with the following variables:

```env
# Server Configuration
PORT=5000
DEBUG=false

# Security (CHANGE THESE!)
SECRET_KEY=your-very-secret-key-here-min-32-chars
JWT_SECRET=your-jwt-secret-key-here-min-32-chars

# JWT Settings
JWT_EXPIRE_HOURS=24
JWT_REFRESH_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_COUNT=5
RATE_LIMIT_WINDOW=10800
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW=900

# VM Settings
VM_LIFETIME_HOURS=6
CLEANUP_INTERVAL=300

# GitHub API
GITHUB_API_BASE=https://api.github.com
GITHUB_TIMEOUT=15
GITHUB_RETRY_COUNT=3
GITHUB_POOL_SIZE=20

# Cache & Performance
CACHE_TTL=5
MAX_WORKERS=10
COMPRESS_LEVEL=6
BCRYPT_ROUNDS=12

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:5000,http://localhost:3000
```

---

📡 API Documentation

Authentication Endpoints

Method Endpoint Description Auth
POST /api/auth/register Register new user ❌
POST /api/auth/login Login user ❌
POST /api/auth/logout Logout user ✅
GET /api/auth/me Get current user ✅
POST /api/auth/refresh Refresh access token ❌

VPS Endpoints

Method Endpoint Description Auth
GET /api/vps List user's VMs ✅
POST /api/vps Create new VM ✅
GET /api/vps/<id> Get VM details ✅
DELETE /api/vps/<id> Delete VM ✅
GET /api/stats Get statistics ✅

Example: Create VM

```bash
curl -X POST http://localhost:5000/api/vps \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "githubToken": "ghp_xxxx",
    "tailscaleKey": "tskey-xxxx",
    "osType": "ubuntu",
    "vmUsername": "forest_user",
    "vmPassword": "secure_password"
  }'
```

Response

```json
{
  "success": true,
  "id": "abc12345",
  "name": "natural-forest_user-abc12345",
  "osType": "ubuntu",
  "username": "forest_user",
  "password": "secure_password",
  "status": "creating",
  "repoUrl": "https://github.com/user/vps-abc12345",
  "createdAt": "2024-01-15T10:30:00Z",
  "expiresAt": "2024-01-15T16:30:00Z"
}
```

---

📁 Project Structure

```
natural-vps/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── run.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── auth.py
│   ├── vps.py
│   ├── utils.py
│   └── templates/
│       └── index.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── assets/
├── data/
└── logs/
```

---

🤝 Contributing

We welcome contributions! Here's how you can help:

🌱 Ways to Contribute

1. 🐛 Report Bugs - Open an issue with detailed description
2. 💡 Suggest Features - Share your ideas in discussions
3. 📝 Improve Documentation - Fix typos or add examples
4. 💻 Submit Code - Fork, branch, and create a pull request

Development Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/natural-vps.git
cd natural-vps

# Create branch
git checkout -b feature/amazing-feature

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Submit PR
git push origin feature/amazing-feature
```

---

📞 Contact & Support

<div align="center">Channel Information
📧 Email thienantran1268@gmail.com
💬 Discord superdzan
🐙 GitHub @TDz888


Feel free to reach out for questions, suggestions, or just to say hi!

</div>---

📄 License

Distributed under the MIT License. See LICENSE for more information.

```
MIT License

Copyright (c) 2024 Natural VPS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

<div align="center"><br/><img src="https://images.pexels.com/photos/355465/pexels-photo-355465.jpeg" width="100" style="border-radius: 50%; opacity: 0.7;" /><br/>
  <br/><i>Made with 💚 for nature and technology</i>

<br/>
  <br/>https://img.shields.io/github/stars/TDz888/natural-vps?style=social
https://img.shields.io/github/forks/TDz888/natural-vps?style=social

<br/><sub>🌿 Plant a VM • Grow your forest • Connect with nature 🌿</sub>

</div>
```
