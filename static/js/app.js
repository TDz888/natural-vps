// Natural VPS - Main JavaScript

const API_BASE = window.location.origin;

// State
let currentUser = null;
let authToken = null;

// ============================================
// AUTHENTICATION
// ============================================

async function register(username, password, email = null) {
    try {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email })
        });
        
        const data = await res.json();
        
        if (data.success) {
            currentUser = data.user;
            showToast('Registration successful! Welcome to Natural VPS', 'success');
            showMainApp();
            loadVMs();
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
            showToast('Welcome back!', 'success');
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
        currentUser = null;
        hideMainApp();
        showToast('Logged out successfully', 'info');
    } catch (e) {
        // Still logout locally
        currentUser = null;
        hideMainApp();
    }
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
    const container = document.getElementById('toastContainer') || createToastContainer();
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
        <span>${message}</span>
        <span style="cursor:pointer; opacity:0.5;" onclick="this.parentElement.remove()">×</span>
    `;
    
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function showMainApp() {
    document.querySelector('.auth-container').style.display = 'none';
    document.querySelector('.main-app').classList.add('visible');
    document.getElementById('userDisplayName').textContent = currentUser?.username || '';
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

async function createVM(formData) {
    const btn = document.getElementById('createBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating...';
    
    try {
        const res = await fetch(`${API_BASE}/api/vps`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await res.json();
        
        if (data.success) {
            showToast(`VM "${data.name}" created!`, 'success');
            loadVMs();
            loadStats();
            
            // Clear form
            document.getElementById('githubToken').value = '';
            document.getElementById('tailscaleKey').value = '';
            document.getElementById('vmUsername').value = generateUsername();
            document.getElementById('vmPassword').value = generatePassword();
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
        <div class="vm-item" onclick="showVMDetails('${vm.id}')">
            <div class="vm-header">
                <div class="vm-info">
                    <div class="vm-icon">
                        <i class="fab fa-${vm.osType === 'ubuntu' ? 'ubuntu' : 'windows'}"></i>
                    </div>
                    <div>
                        <div class="vm-name">${vm.name}</div>
                        <div class="vm-os">${vm.status} • ${formatRelativeTime(vm.createdAt)}</div>
                    </div>
                </div>
                <i class="fas fa-chevron-right" style="color: var(--leaf-green);"></i>
            </div>
        </div>
    `).join('');
}

// ============================================
// UTILITIES
// ============================================

function generateUsername() {
    const prefixes = ['forest', 'leaf', 'river', 'stone', 'wind', 'sun'];
    return prefixes[Math.floor(Math.random() * prefixes.length)] + '_' + 
           Math.random().toString(36).substring(2, 8);
}

function generatePassword() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    return Array(14).fill(0).map(() => chars[Math.floor(Math.random() * chars.length)]).join('');
}

function formatRelativeTime(date) {
    const diff = Math.floor((new Date() - new Date(date)) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
    // Check if already logged in
    const isLoggedIn = await checkAuth();
    
    if (!isLoggedIn) {
        // Show auth container
        document.querySelector('.auth-container').style.display = 'flex';
    }
    
    // Setup event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Register form
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const password = document.getElementById('regPassword').value;
        const email = document.getElementById('regEmail').value;
        
        await register(username, password, email);
    });
    
    // Login form
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const remember = document.getElementById('rememberMe').checked;
        
        await login(username, password, remember);
    });
    
    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', logout);
    
    // Create VM button
    document.getElementById('createBtn').addEventListener('click', () => {
        const formData = {
            githubToken: document.getElementById('githubToken').value,
            tailscaleKey: document.getElementById('tailscaleKey').value,
            osType: document.querySelector('.os-option.active')?.dataset.os || 'ubuntu',
            vmUsername: document.getElementById('vmUsername').value,
            vmPassword: document.getElementById('vmPassword').value
        };
        createVM(formData);
    });
    
    // Generate username/password
    document.getElementById('randomUserBtn').addEventListener('click', () => {
        document.getElementById('vmUsername').value = generateUsername();
    });
    
    document.getElementById('randomPassBtn').addEventListener('click', () => {
        document.getElementById('vmPassword').value = generatePassword();
    });
}
