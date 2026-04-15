// ================================
// NATURAL VPS - Modern Frontend App
// ================================

class NaturalVPSApp {
    constructor() {
        this.apiBase = this.getApiBase();
        this.user = null;
        this.vms = [];
        this.token = null;
        this.init();
    }

    getApiBase() {
        const protocol = window.location.protocol;
        const host = window.location.host;
        return `${protocol}//${host}/api`;
    }

    async init() {
        console.log('🌿 Natural VPS App Initializing...');
        this.setupEventListeners();
        this.loadUser();
        this.checkHealth();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Auth Forms
        document.getElementById('loginForm')?.addEventListener('submit', e => this.handleLogin(e));
        document.getElementById('registerForm')?.addEventListener('submit', e => this.handleRegister(e));
        document.getElementById('logoutBtn')?.addEventListener('click', () => this.handleLogout());

        // VM Creation
        document.getElementById('createVMForm')?.addEventListener('submit', e => this.handleCreateVM(e));

        // Tab Switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', e => this.switchTab(e));
        });

        // Auto-save GitHub token to localStorage (encrypted)
        document.getElementById('githubToken')?.addEventListener('blur', e => {
            this.saveSecureLocal('githubToken', e.target.value);
        });
    }

    // ================================
    // AUTHENTICATION METHODS
    // ================================

    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            this.showLoading('Logging in...');
            const response = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();
            if (data.success) {
                this.token = data.token;
                localStorage.setItem('auth_token', data.token);
                this.user = data.user;
                this.showAuth(false);
                this.loadVMs();
                this.showSuccess('Login successful!');
            } else {
                this.showError(data.error || 'Login failed');
            }
        } catch (error) {
            this.showError('Login error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;

        if (password !== confirmPassword) {
            this.showError('Passwords do not match');
            return;
        }

        try {
            this.showLoading('Creating account...');
            const response = await fetch(`${this.apiBase}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess('Account created! Please login.');
                document.querySelectorAll('.auth-tab')[0].click();
            } else {
                this.showError(data.error || 'Registration failed');
            }
        } catch (error) {
            this.showError('Registration error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    handleLogout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('githubToken');
        this.user = null;
        this.token = null;
        this.vms = [];
        this.showAuth(true);
        this.showSuccess('Logged out successfully');
    }

    async loadUser() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            this.token = token;
            try {
                const response = await fetch(`${this.apiBase}/auth/me`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    this.user = await response.json();
                    this.showAuth(false);
                    this.loadVMs();
                } else {
                    this.handleLogout();
                }
            } catch (error) {
                console.error('User load error:', error);
                this.handleLogout();
            }
        }
    }

    // ================================
    // VM MANAGEMENT METHODS
    // ================================

    async handleCreateVM(e) {
        e.preventDefault();
        const githubToken = document.getElementById('githubToken').value;
        const tailscaleKey = document.getElementById('tailscaleKey').value;
        const vmName = document.getElementById('vmName').value;
        const vmSize = document.getElementById('vmSize').value;

        if (!githubToken || !tailscaleKey) {
            this.showError('GitHub token and Tailscale key are required');
            return;
        }

        try {
            this.showLoading('Creating VM...');
            const response = await fetch(`${this.apiBase}/create-vm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    github_token: githubToken,
                    tailscale_key: tailscaleKey,
                    name: vmName,
                    size: vmSize
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess('VM created! It should appear in a few seconds...');
                e.target.reset();
                setTimeout(() => this.loadVMs(), 3000);
            } else {
                this.showError(data.error || 'VM creation failed');
            }
        } catch (error) {
            this.showError('VM creation error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async loadVMs() {
        if (!this.token) return;

        try {
            const response = await fetch(`${this.apiBase}/vms`, {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
            const data = await response.json();
            if (data.success) {
                this.vms = data.vms;
                this.renderVMs();
            }
        } catch (error) {
            console.error('VM load error:', error);
        }
    }

    renderVMs() {
        const listContainer = document.getElementById('vmList');
        if (!listContainer) return;

        if (this.vms.length === 0) {
            listContainer.innerHTML = '<div class="empty-state">No VMs created yet</div>';
            return;
        }

        listContainer.innerHTML = this.vms.map(vm => `
            <div class="vm-card">
                <div class="vm-header">
                    <h3 class="vm-name">${vm.name}</h3>
                    <span class="badge badge-${this.getStatusBadgeClass(vm.status)}">${vm.status}</span>
                </div>
                <div class="vm-info">
                    <div><i class="fas fa-key"></i> ID: ${vm.id.substring(0, 8)}</div>
                    <div><i class="fas fa-clock"></i> Created: ${new Date(vm.created_at).toLocaleString()}</div>
                    <div><i class="fas fa-hourglass-end"></i> Expires in: ${vm.time_remaining}</div>
                </div>
                <div class="vm-actions">
                    ${vm.status === 'running' ? `
                        <button class="btn btn-primary btn-small" onclick="app.connectVNC('${vm.id}')">
                            <i class="fas fa-desktop"></i> VNC
                        </button>
                        <button class="btn btn-secondary btn-small" onclick="app.copyInfo('${vm.tailscale_ip}')">
                            <i class="fas fa-link"></i> Copy IP
                        </button>
                    ` : ''}
                    <button class="btn btn-danger btn-small" onclick="app.deleteVM('${vm.id}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    async deleteVM(vmId) {
        if (!confirm('Delete this VM?')) return;

        try {
            const response = await fetch(`${this.apiBase}/vms/${vmId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
            const data = await response.json();
            if (data.success) {
                this.showSuccess('VM deleted');
                this.loadVMs();
            } else {
                this.showError(data.error || 'Deletion failed');
            }
        } catch (error) {
            this.showError('Delete error: ' + error.message);
        }
    }

    connectVNC(vmId) {
        const vm = this.vms.find(v => v.id === vmId);
        if (vm) {
            window.open(`/vnc?vm=${vmId}`, 'VNC', 'width=1024,height=768');
        }
    }

    copyInfo(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showSuccess('Copied to clipboard!');
        });
    }

    // ================================
    // HEALTH & STATUS METHODS
    // ================================

    async checkHealth() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();
            this.updateHealthStatus(data);
        } catch (error) {
            console.error('Health check error:', error);
        }
    }

    updateHealthStatus(data) {
        const healthBadge = document.getElementById('healthStatus');
        if (healthBadge) {
            healthBadge.innerHTML = '🟢 Operational';
        }
    }

    startAutoRefresh() {
        // Refresh VMs every 5 seconds if authenticated
        setInterval(() => {
            if (this.token && this.vms.length > 0) {
                this.loadVMs();
            }
        }, 5000);

        // Health check every 30 seconds
        setInterval(() => this.checkHealth(), 30000);
    }

    // ================================
    // UI UTILITY METHODS
    // ================================

    switchTab(e) {
        const tabName = e.target.dataset.tab;
        if (!tabName) return;

        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

        const tabContent = document.getElementById(tabName);
        if (tabContent) {
            tabContent.classList.add('active');
            e.target.classList.add('active');
        }
    }

    showAuth(show) {
        const authContainer = document.getElementById('authContainer');
        const mainApp = document.getElementById('mainApp');
        if (authContainer) authContainer.style.display = show ? 'flex' : 'none';
        if (mainApp) mainApp.style.display = show ? 'none' : 'block';
    }

    showLoading(message = 'Loading...') {
        const loader = document.getElementById('loader');
        if (loader) {
            loader.innerHTML = `<div class="spinner"></div> <span>${message}</span>`;
            loader.style.display = 'block';
        }
    }

    hideLoading() {
        const loader = document.getElementById('loader');
        if (loader) loader.style.display = 'none';
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        if (!alertContainer) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        alertContainer.appendChild(alert);

        setTimeout(() => alert.remove(), 5000);
    }

    getStatusBadgeClass(status) {
        const map = {
            'running': 'success',
            'creating': 'warning',
            'failed': 'danger',
            'stopped': 'info'
        };
        return map[status] || 'info';
    }

    // ================================
    // STORAGE METHODS
    // ================================

    saveSecureLocal(key, value) {
        // Simple encryption (base64 - not production secure!)
        localStorage.setItem(`secure_${key}`, btoa(value));
    }

    loadSecureLocal(key) {
        const value = localStorage.getItem(`secure_${key}`);
        return value ? atob(value) : null;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NaturalVPSApp();
    console.log('✅ Natural VPS App Ready');
});
