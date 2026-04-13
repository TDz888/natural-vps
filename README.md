<div align="center">
  <img src="https://images.pexels.com/photos/957024/forest-trees-perspective-bare-trees-957024.jpg" alt="Natural VPS Banner" width="100%" style="border-radius: 20px; opacity: 0.8;" />
  
  # 🌿 NATURAL VPS
  
  *Cinematic Nature 4K • Sustainable Computing*
  
  [![Version](https://img.shields.io/badge/version-2.1.0-6b8e4e?style=for-the-badge)](https://github.com/yourusername/natural-vps)
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

## 🌲 **About The Project**

Natural VPS is a beautiful, cinematic VPS management platform that combines the power of GitHub Actions with the serenity of nature. Create and manage virtual machines through an intuitive interface inspired by forests, rivers, and the tranquility of the natural world.

> *"Just as a forest grows one tree at a time, your virtual infrastructure grows one VM at a time."*

### ✨ **Why Natural VPS?**

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

## 🍃 **Table of Contents**

- [Screenshots](#-screenshots)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Docker Installation](#docker-installation)
  - [Manual Installation](#manual-installation)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 📸 **Screenshots**

<div align="center">
  <table>
    <tr>
      <td><img src="https://via.placeholder.com/400x250/1a3a2a/e8e4d9?text=Login+Screen" alt="Login Screen"/></td>
      <td><img src="https://via.placeholder.com/400x250/1a3a2a/e8e4d9?text=Dashboard" alt="Dashboard"/></td>
    </tr>
    <tr>
      <td><img src="https://via.placeholder.com/400x250/1a3a2a/e8e4d9?text=Create+VM" alt="Create VM"/></td>
      <td><img src="https://via.placeholder.com/400x250/1a3a2a/e8e4d9?text=VM+List" alt="VM List"/></td>
    </tr>
  </table>
</div>

---

## 🌿 **Features**

### 🔐 **Authentication & Security**
- [x] User registration with email validation
- [x] Secure login with JWT tokens
- [x] bcrypt password hashing (12 rounds)
- [x] HTTP-only cookies for token storage
- [x] Rate limiting (5 VMs / 3 hours / IP)
- [x] Login attempt tracking & brute-force protection
- [x] CORS protection with configurable origins
- [x] Security headers (CSP, HSTS, XSS protection)

### 🖥️ **VPS Management**
- [x] Create VMs on GitHub Actions runners
- [x] Support for Ubuntu 22.04 and Windows Server 2022
- [x] Automatic Tailscale VPN setup
- [x] Cloudflare Tunnel for public VNC access
- [x] Real-time VM status tracking
- [x] One-click VM deletion
- [x] VM statistics dashboard
- [x] Custom username/password generation

### ⚡ **Performance Optimizations**
- [x] Connection pooling for GitHub API (20 connections)
- [x] SQLite WAL mode for concurrent access
- [x] Redis caching (with in-memory fallback)
- [x] Thread pool for background tasks
- [x] Response compression (gzip/brotli)
- [x] Database indexing for fast queries
- [x] Retry logic with exponential backoff
- [x] Async logging with QueueHandler

### 🎨 **User Experience**
- [x] Cinematic 4K nature video background
- [x] Smooth animations on every interaction
- [x] Animated leaves and sunrays
- [x] Glassmorphism design
- [x] Fully responsive layout
- [x] Toast notifications
- [x] Keyboard shortcuts
- [x] Dark/light mode (nature-inspired palette)

---

## 🛠️ **Tech Stack**

<div align="center">

| Category | Technology | Purpose |
|:--------:|:----------:|:--------|
| **Backend** | Flask 3.0 | Web framework |
| **Database** | SQLite + WAL | Data persistence |
| **Cache** | Redis (optional) | Performance |
| **Auth** | JWT + bcrypt | Security |
| **Server** | Gunicorn | Production WSGI |
| **Frontend** | HTML5/CSS3/JS | User interface |
| **Icons** | Font Awesome 6 | Visual elements |
| **Fonts** | Cormorant Garamond | Elegant typography |
| **Container** | Docker + Compose | Deployment |

</div>

---

## 🚀 **Getting Started**

### Prerequisites

- **GitHub Account** with a [Personal Access Token](https://github.com/settings/tokens)
  - Required scopes: `repo`, `workflow`
- **Tailscale Account** with an [Auth Key](https://login.tailscale.com/admin/settings/keys)
- **Docker** (recommended) or Python 3.11+

### 🐳 **Docker Installation** *(Recommended)*

```bash
# Clone the repository
git clone https://github.com/yourusername/natural-vps.git
cd natural-vps

# Copy environment file
cp .env.example .env

# Edit .env with your secrets
nano .env

# Start the application
docker-compose up -d --build
