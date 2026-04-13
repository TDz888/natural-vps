// Natural VPS - Complete JavaScript

const API_BASE = window.location.origin;

// State
let currentUser = null;
let selectedOS = 'ubuntu';

// ============================================
// AUTHENTICATION
// ============================================

async function register(username, password, email = null) {
    try {
        const confirmPassword = document.getElementById('regConfirmPassword').value;
        
        if (password !== confirmPassword) {
            showToast('Passwords do not match', 'error');
            return false;
        }
        
        if (password.length < 8) {
            showToast('Password must be at least 8 characters', 'error');
            return false;
        }
        
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email })
        });
        
        const data = await res.json();
        
        if (data.success) {
            currentUser = data.user;
            showToast('🌿 Welcome to Natural VPS!', 'success');
            showMainApp();
            loadVMs();
            loadStats();
            return true;
        } else {
            showToast(data.error, 'error');
            return false;
        }
    } catch (e) {
        showToast('Connection error', 'error');
        return false;
    }
}

async function login(username, password, remember = false) {
    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, remember })
        });
        
        const data = await res.json();
        
        if (data.success) {
            currentUser = data.user;
            showToast('🍃 Welcome back!', 'success');
            showMainApp();
            loadVMs();
            loadStats();
            return true;
        } else {
            showToast(data.error, 'error');
            return false;
        }
    } catch (e) {
        showToast('Connection error', 'error');
        return false;
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST' });
    } catch (e) {
        // Ignore
    }
    
    currentUser = null;
    hideMainApp();
    showToast('Logged out', 'info');
}

async function checkAuth() {
    try {
        const res = await fetch(`${API_BASE}/api/auth/me`);
        const data = await res.json();
        
        if (data.success) {
            currentUser = data.user;
            showMainApp();
            loadVMs();
            loadStats();
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

// ============================================
// UI FUNCTIONS
// ============================================

function showToast(message, type = 'info', duration = 4000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span class="toast-message">${message}</span>
        <span style="cursor:pointer; opacity:0.5; margin-left:auto;" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </span>
    `;
    
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function showMainApp() {
    document.querySelector('.auth-container').style.display = 'none';
    document.querySelector('.main-app').classList.add('visible');
    document.getElementById('userDisplayName').textContent = currentUser?.username || 'User';
    document.getElementById('userAvatar').textContent = currentUser?.username?.charAt(0).toUpperCase() || 'U';
}

function hideMainApp() {
    document.querySelector('.auth-container').style.display = 'flex';
    document.querySelector('.main-app').classList.remove('visible');
}

function switchTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    
    document.querySelector(`.auth-tab[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`${tab}Form`).classList.add('active');
}

function selectOS(os) {
    selectedOS = os;
    document.querySelectorAll('.os-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector(`.os-option[data-os="${os}"]`).classList.add('active');
}

// ============================================
// VPS FUNCTIONS
// ============================================

async function loadVMs() {
    try {
        const res = await fetch(`${API_BASE}/api/vps`);
        const data = await res.json();
        
        if (data.success) {
            renderVMList(data.vms);
        }
    } catch (e) {
        console.error('Load VMs error:', e);
    }
}

async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('statTotal').textContent = data.stats.total || 0;
            document.getElementById('statRunning').textContent = data.stats.running || 0;
        }
    } catch (e) {
        console.error('Load stats error:', e);
    }
}

async function createVM() {
    const githubToken = document.getElementById('githubToken').value.trim();
    const tailscaleKey = document.getElementById('tailscaleKey').value.trim();
    let username = document.getElementById('vmUsername').value.trim();
    let password = document.getElementById('vmPassword').value;
    
    if (!githubToken) {
        showToast('GitHub Token is required', 'error');
        return;
    }
    
    if (!tailscaleKey) {
        showToast('Tailscale Key is required', 'error');
        return;
    }
    
    if (!username) {
        username = generateUsername();
        document.getElementById('vmUsername').value = username;
    }
    
    if (!password) {
        password = generatePassword();
        document.getElementById('vmPassword').value = password;
    }
    
    const btn = document.getElementById('createBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Planting...';
    
    try {
        const res = await fetch(`${API_BASE}/api/vps`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                githubToken,
                tailscaleKey,
                osType: selectedOS,
                vmUsername: username,
                vmPassword: password
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            showToast(`🌱 VM "${data.name}" is growing!`, 'success');
            
            // Clear sensitive fields
            document.getElementById('githubToken').value = '';
            document.getElementById('tailscaleKey').value = '';
            document.getElementById('vmUsername').value = generateUsername();
            document.getElementById('vmPassword').value = generatePassword();
            
            loadVMs();
            loadStats();
        } else {
            showToast(data.error, 'error');
        }
    } catch (e) {
        showToast('Connection error', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-seedling"></i> Grow New VM';
    }
}

function renderVMList(vms) {
    const container = document.getElementById('vmList');
    
    if (!vms || vms.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon"><i class="fas fa-seedling"></i></div>
                <div>Your virtual forest is empty</div>
                <div style="font-size: 0.8rem; margin-top: 10px;">Plant your first VM to begin</div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = vms.map(vm => `
        <div class="vm-item">
            <div class="vm-header">
                <div class="vm-info">
                    <div class="vm-icon">
                        <i class="fab fa-${vm.osType === 'ubuntu' ? 'ubuntu' : 'windows'}"></i>
                    </div>
                    <div>
                        <div class="vm-name">${vm.name}</div>
                        <div class="vm-os">
                            <span class="status-badge" style="color: ${vm.status === 'running' ? '#8fbc6a' : '#d4af37'};">●</span>
                            ${vm.status} • ${formatRelativeTime(vm.createdAt)}
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    ${vm.cloudflareUrl ? `
                        <a href="${vm.cloudflareUrl}" target="_blank" style="color: #8fbc6a; text-decoration: none;" title="Open VNC">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    ` : ''}
                    <button onclick="deleteVM('${vm.id}')" style="background: none; border: none; color: #c06060; cursor: pointer;" title="Delete VM">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

async function deleteVM(vmId) {
    if (!confirm('Are you sure you want to delete this VM?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/vps/${vmId}`, { method: 'DELETE' });
        const data = await res.json();
        
        if (data.success) {
            showToast('VM removed from your forest', 'success');
            loadVMs();
            loadStats();
        } else {
            showToast(data.error, 'error');
        }
    } catch (e) {
        showToast('Connection error', 'error');
    }
}

// ============================================
// UTILITIES
// ============================================

function generateUsername() {
    const prefixes = ['forest', 'leaf', 'river', 'stone', 'wind', 'sun', 'moss', 'pine'];
    return prefixes[Math.floor(Math.random() * prefixes.length)] + '_' + 
           Math.random().toString(36).substring(2, 8);
}

function generatePassword(length = 14) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    return Array(length).fill(0).map(() => chars[Math.floor(Math.random() * chars.length)]).join('');
}

function formatRelativeTime(date) {
    if (!date) return 'just now';
    const diff = Math.floor((new Date() - new Date(date)) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Register form
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername').value.trim();
        const password = document.getElementById('regPassword').value;
        const email = document.getElementById('regEmail').value.trim();
        
        await register(username, password, email || null);
    });
    
    // Login form
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const remember = document.getElementById('rememberMe').checked;
        
        await login(username, password, remember);
    });
    
    // Logout
    document.getElementById('logoutBtn').addEventListener('click', logout);
    
    // Create VM
    document.getElementById('createBtn').addEventListener('click', createVM);
    
    // Refresh
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadVMs();
        loadStats();
        showToast('Forest refreshed', 'info');
    });
    
    // Generate buttons
    document.getElementById('randomUserBtn').addEventListener('click', () => {
        document.getElementById('vmUsername').value = generateUsername();
    });
    
    document.getElementById('randomPassBtn').addEventListener('click', () => {
        document.getElementById('vmPassword').value = generatePassword();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            // Close any open modals
        }
    });
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    // Set initial values
    document.getElementById('vmUsername').value = generateUsername();
    document.getElementById('vmPassword').value = generatePassword();
    
    // Check if already logged in
    const isLoggedIn = await checkAuth();
    
    if (!isLoggedIn) {
        document.querySelector('.auth-container').style.display = 'flex';
    }
    
    setupEventListeners();
});

// Make functions available globally
window.selectOS = selectOS;
window.deleteVM = deleteVM;
