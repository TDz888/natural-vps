/* ============================================ */
/* NATURAL VPS - MAIN JAVASCRIPT                */
/* API Endpoint: Auto-detected from URL         */
/* ============================================ */

const API_BASE = window.location.origin;

let currentUser = null;
let vms = [];
let selectedOS = 'ubuntu';
let progressInterval = null;
let rateLimitInterval = null;

const DOM = {
    authContainer: document.querySelector('.auth-container'),
    mainApp: document.querySelector('.main-app'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    loginUsername: document.getElementById('loginUsername'),
    loginPassword: document.getElementById('loginPassword'),
    regUsername: document.getElementById('regUsername'),
    regPassword: document.getElementById('regPassword'),
    regConfirmPassword: document.getElementById('regConfirmPassword'),
    userAvatar: document.getElementById('userAvatar'),
    userDisplayName: document.getElementById('userDisplayName'),
    logoutBtn: document.getElementById('logoutBtn'),
    githubToken: document.getElementById('githubToken'),
    tailscaleKey: document.getElementById('tailscaleKey'),
    vmUsername: document.getElementById('vmUsername'),
    vmPassword: document.getElementById('vmPassword'),
    createBtn: document.getElementById('createBtn'),
    vmList: document.getElementById('vmList'),
    statTotal: document.getElementById('statTotal'),
    statRunning: document.getElementById('statRunning'),
    refreshBtn: document.getElementById('refreshBtn'),
    progressContainer: document.getElementById('createProgressContainer'),
    progressFill: document.getElementById('createProgressFill'),
    progressMessage: document.getElementById('createProgressMessage'),
    progressPercent: document.getElementById('createProgressPercent'),
    progressSteps: document.querySelectorAll('.progress-step'),
    vmModal: document.getElementById('vmModal'),
    modalVmName: document.getElementById('modalVmName'),
    modalVmBody: document.getElementById('modalVmBody'),
    rateLimitContainer: document.getElementById('rateLimitContainer'),
    rateLimitUsed: document.getElementById('rateLimitUsed'),
    rateLimitTotal: document.getElementById('rateLimitTotal'),
    rateLimitFill: document.getElementById('rateLimitFill'),
    rateLimitTime: document.getElementById('rateLimitTime'),
    rateLimitWarning: document.getElementById('rateLimitWarning')
};

function showToast(message, type = 'info', duration = 4000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
    toast.innerHTML = `<i class="fas ${icons[type]}"></i><span class="toast-message">${message}</span><span class="toast-close" onclick="this.parentElement.remove()">×</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, duration);
}

function generateUsername() {
    const prefixes = ['forest', 'leaf', 'river', 'stone', 'wind', 'sun'];
    return prefixes[Math.floor(Math.random() * prefixes.length)] + '_' + Math.random().toString(36).substring(2, 8);
}

function generatePassword() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    return Array(14).fill(0).map(() => chars[Math.floor(Math.random() * chars.length)]).join('');
}

function formatRelativeTime(dateString) {
    if (!dateString) return 'just now';
    const diff = Math.floor((new Date() - new Date(dateString)) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

function formatCountdown(expiresAt) {
    if (!expiresAt) return 'N/A';
    const remaining = new Date(expiresAt) - Date.now();
    if (remaining <= 0) return 'Expired';
    const h = Math.floor(remaining / 3600000);
    const m = Math.floor((remaining % 3600000) / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    return `${h}h ${m}m ${s}s`;
}

async function register(username, password) {
    try {
        if (password !== DOM.regConfirmPassword.value) { showToast('Passwords do not match', 'error'); return false; }
        if (password.length < 8) { showToast('Password must be at least 8 characters', 'error'); return false; }
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            currentUser = data.user;
            showToast('🌿 Welcome to Natural VPS!', 'success');
            showMainApp();
            loadVMs(); loadStats(); loadRateLimit();
            return true;
        } else { showToast(data.error, 'error'); return false; }
    } catch (e) { showToast('Connection error', 'error'); return false; }
}

async function login(username, password) {
    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            currentUser = data.user;
            showToast('🍃 Welcome back!', 'success');
            showMainApp();
            loadVMs(); loadStats(); loadRateLimit();
            return true;
        } else { showToast(data.error, 'error'); return false; }
    } catch (e) { showToast('Connection error', 'error'); return false; }
}

async function logout() {
    try { await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include' }); } catch (e) {}
    currentUser = null;
    hideMainApp();
    showToast('Logged out', 'info');
}

async function checkAuth() {
    try {
        const res = await fetch(`${API_BASE}/api/auth/me`, { credentials: 'include' });
        const data = await res.json();
        if (data.success) { currentUser = data.user; showMainApp(); loadVMs(); loadStats(); loadRateLimit(); return true; }
        return false;
    } catch (e) { return false; }
}

function showMainApp() {
    DOM.authContainer.style.display = 'none';
    DOM.mainApp.classList.add('visible');
    DOM.userDisplayName.textContent = currentUser?.username || 'User';
    DOM.userAvatar.textContent = currentUser?.username?.charAt(0).toUpperCase() || 'U';
}

function hideMainApp() {
    DOM.authContainer.style.display = 'flex';
    DOM.mainApp.classList.remove('visible');
}

function switchTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
    document.querySelector(`.auth-tab[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`${tab}Form`).classList.add('active');
}

async function loadVMs() {
    try {
        const res = await fetch(`${API_BASE}/api/vps`, { credentials: 'include' });
        if (!res.ok) return;
        const data = await res.json();
        if (data.success) { vms = data.vms || []; renderVMList(vms); }
    } catch (e) { console.error('Load VMs error:', e); }
}

async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`, { credentials: 'include' });
        if (!res.ok) return;
        const data = await res.json();
        if (data.success) { DOM.statTotal.textContent = data.stats.total || 0; DOM.statRunning.textContent = data.stats.running || 0; }
    } catch (e) { console.error('Load stats error:', e); }
}

async function loadRateLimit() {
    if (!currentUser) return;
    try {
        const res = await fetch(`${API_BASE}/api/rate-limit`, { credentials: 'include' });
        if (!res.ok) return;
        const data = await res.json();
        if (data.success) {
            const rl = data.rate_limit;
            if (DOM.rateLimitContainer) DOM.rateLimitContainer.style.display = 'block';
            DOM.rateLimitUsed.textContent = rl.used;
            DOM.rateLimitTotal.textContent = rl.limit;
            const percent = (rl.used / rl.limit) * 100;
            DOM.rateLimitFill.style.width = percent + '%';
            DOM.rateLimitFill.classList.remove('warning', 'danger');
            if (percent >= 80) DOM.rateLimitFill.classList.add('danger');
            else if (percent >= 60) DOM.rateLimitFill.classList.add('warning');
            
            if (rl.remaining === 0) {
                DOM.rateLimitWarning.style.display = 'flex';
                DOM.rateLimitWarning.innerHTML = '<i class="fas fa-ban"></i><span>Limit reached! Wait for reset.</span>';
                DOM.rateLimitWarning.style.color = '#e08080';
            } else if (rl.remaining <= 2) {
                DOM.rateLimitWarning.style.display = 'flex';
                DOM.rateLimitWarning.innerHTML = `<i class="fas fa-exclamation-triangle"></i><span>Only ${rl.remaining} VM${rl.remaining > 1 ? 's' : ''} left!</span>`;
                DOM.rateLimitWarning.style.color = '#d4af37';
            } else {
                DOM.rateLimitWarning.style.display = 'none';
            }
            
            let seconds = rl.seconds_remaining;
            const updateTimer = () => {
                if (seconds > 0) {
                    const h = Math.floor(seconds / 3600);
                    const m = Math.floor((seconds % 3600) / 60);
                    const s = seconds % 60;
                    DOM.rateLimitTime.textContent = h > 0 ? `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}` : `${m}:${s.toString().padStart(2, '0')}`;
                } else {
                    DOM.rateLimitTime.textContent = 'Reset now';
                }
            };
            updateTimer();
            if (rateLimitInterval) clearInterval(rateLimitInterval);
            rateLimitInterval = setInterval(() => { if (seconds > 0) { seconds--; updateTimer(); } else { clearInterval(rateLimitInterval); } }, 1000);
        }
    } catch (e) { console.error('Rate limit error:', e); }
}

function renderVMList(vmArray) {
    if (!vmArray || vmArray.length === 0) {
        DOM.vmList.innerHTML = `<div class="empty-state"><div class="empty-icon"><i class="fas fa-seedling"></i></div><p>Your virtual forest is empty</p><small>Plant your first VM to begin</small></div>`;
        return;
    }
    DOM.vmList.innerHTML = vmArray.map(vm => {
        const statusClass = vm.status === 'running' ? 'running' : (vm.status === 'creating' ? 'creating' : 'expired');
        return `<div class="vm-item" onclick="showVmModal('${vm.id}')">
            <div class="vm-header"><div class="vm-info"><div class="vm-icon"><i class="fab fa-${vm.osType === 'ubuntu' ? 'ubuntu' : 'windows'}"></i></div>
            <div><div class="vm-name">${vm.name || vm.id}</div><div class="vm-meta"><span class="vm-status-dot ${statusClass}"></span><span class="vm-status-text">${vm.status}</span><span class="vm-time">• ${formatRelativeTime(vm.createdAt)}</span></div></div></div>
            <i class="fas fa-chevron-right vm-arrow"></i></div></div>`;
    }).join('');
}

function updateProgressUI(step, percent, message) {
    DOM.progressFill.style.width = percent + '%';
    const msgSpan = DOM.progressMessage.querySelector('span') || DOM.progressMessage;
    if (msgSpan.tagName === 'SPAN') msgSpan.textContent = message;
    else DOM.progressMessage.innerHTML = `<span>${message}</span>`;
    DOM.progressPercent.textContent = percent + '%';
    DOM.progressSteps.forEach((s, index) => { s.classList.remove('active', 'completed'); if (index < step) s.classList.add('completed'); else if (index === step) s.classList.add('active'); });
}

function startProgressTracking(vmId) {
    updateProgressUI(0, 5, '🔐 Validating token...');
    if (progressInterval) clearInterval(progressInterval);
    progressInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/vps/${vmId}/progress`, { credentials: 'include' });
            if (!res.ok) return;
            const data = await res.json();
            if (data.success) {
                const progress = data.progress;
                updateProgressUI(progress.step, progress.percent, progress.message);
                if (progress.status === 'failed') {
                    clearInterval(progressInterval); progressInterval = null;
                    DOM.progressSteps[progress.step]?.classList.add('failed');
                    showToast(`❌ ${progress.error || 'Creation failed'}`, 'error');
                    setTimeout(() => DOM.progressContainer.style.display = 'none', 10000);
                } else if (progress.status === 'completed' || data.vm.status === 'running') {
                    clearInterval(progressInterval); progressInterval = null;
                    loadVMs(); loadStats(); loadRateLimit();
                    showToast(`🌿 VM is ready!`, 'success');
                    setTimeout(() => DOM.progressContainer.style.display = 'none', 3000);
                }
            }
        } catch (e) { console.error('Progress error:', e); }
    }, 2000);
}

async function createVM() {
    const githubToken = DOM.githubToken.value.trim();
    const tailscaleKey = DOM.tailscaleKey.value.trim();
    let username = DOM.vmUsername.value.trim();
    let password = DOM.vmPassword.value;
    if (!githubToken) { showToast('GitHub Token required', 'error'); return; }
    if (!tailscaleKey) { showToast('Tailscale Key required', 'error'); return; }
    if (!username) { username = generateUsername(); DOM.vmUsername.value = username; }
    if (!password) { password = generatePassword(); DOM.vmPassword.value = password; }
    DOM.createBtn.disabled = true;
    DOM.createBtn.innerHTML = '<span class="spinner"></span> Planting...';
    DOM.progressContainer.style.display = 'block';
    updateProgressUI(0, 2, '🔐 Initializing...');
    try {
        const res = await fetch(`${API_BASE}/api/vps`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ githubToken, tailscaleKey, osType: selectedOS, vmUsername: username, vmPassword: password })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`🌱 VM "${data.name}" is growing!`, 'success');
            DOM.githubToken.value = ''; DOM.tailscaleKey.value = '';
            DOM.vmUsername.value = generateUsername(); DOM.vmPassword.value = generatePassword();
            vms.unshift(data); renderVMList(vms);
            startProgressTracking(data.id);
            setTimeout(() => loadRateLimit(), 2000);
        } else { showToast(data.error, 'error'); DOM.progressContainer.style.display = 'none'; }
    } catch (e) { showToast('Connection error', 'error'); DOM.progressContainer.style.display = 'none'; }
    finally { DOM.createBtn.disabled = false; DOM.createBtn.innerHTML = '<i class="fas fa-seedling"></i> Grow New VM'; }
}

async function deleteVM(vmId) {
    if (!confirm('Delete this VM?')) return;
    try {
        const res = await fetch(`${API_BASE}/api/vps/${vmId}`, { method: 'DELETE', credentials: 'include' });
        const data = await res.json();
        if (data.success) {
            showToast('VM deleted', 'success');
            loadVMs(); loadStats(); loadRateLimit();
        }
    } catch (e) { showToast('Error', 'error'); }
}

async function showVmModal(vmId) {
    const vm = vms.find(v => v.id === vmId);
    if (!vm) return;
    DOM.modalVmName.innerHTML = `<i class="fas fa-leaf"></i><span>${vm.name || vmId}</span>`;
    const created = new Date(vm.createdAt).toLocaleString();
    const expires = new Date(vm.expiresAt).toLocaleString();
    const remaining = formatCountdown(vm.expiresAt);
    let statusBadge = vm.status === 'creating' ? '<span class="vm-status-badge creating"><i class="fas fa-spinner fa-pulse"></i> Creating</span>' : (vm.status === 'running' ? '<span class="vm-status-badge live"><i class="fas fa-circle"></i> Live</span>' : '<span class="vm-status-badge offline"><i class="fas fa-circle"></i> Offline</span>');
    let html = `<div style="margin-bottom:20px">${statusBadge}<span class="countdown-timer normal" style="margin-left:10px"><i class="fas fa-hourglass-half"></i> ${remaining}</span></div>
        <div class="info-section"><div class="info-section-title"><i class="fas fa-info-circle"></i> General</div>
        <div class="info-row"><span class="info-label"><i class="fas fa-tag"></i> Name</span><span class="info-value">${vm.name}</span></div>
        <div class="info-row"><span class="info-label"><i class="fas fa-microchip"></i> OS</span><span class="info-value"><i class="fab fa-${vm.osType === 'ubuntu' ? 'ubuntu' : 'windows'}"></i> ${vm.osType}</span></div></div>
        <div class="info-section"><div class="info-section-title"><i class="fas fa-key"></i> Credentials</div>
        <div class="info-row"><span class="info-label"><i class="fas fa-user"></i> Username</span><span class="info-value">${vm.username} <button class="copy-btn" onclick="copyText('${vm.username}', this)"><i class="fas fa-copy"></i></button></span></div>
        <div class="info-row"><span class="info-label"><i class="fas fa-lock"></i> Password</span><span class="info-value">${vm.password} <button class="copy-btn" onclick="copyText('${vm.password}', this)"><i class="fas fa-copy"></i></button></span></div></div>
        <div class="info-section"><div class="info-section-title"><i class="fas fa-network-wired"></i> Connection</div>`;
    if (vm.tailscaleIP) html += `<div class="info-row"><span class="info-label"><i class="fas fa-ip"></i> Tailscale IP</span><span class="info-value">${vm.tailscaleIP} <button class="copy-btn" onclick="copyText('${vm.tailscaleIP}', this)"><i class="fas fa-copy"></i></button></span></div>`;
    if (vm.kamiUrl) html += `<div class="info-row"><span class="info-label"><i class="fas fa-network-wired"></i> Kami Tunnel</span><span class="info-value"><a href="${vm.kamiUrl}" target="_blank">Open VNC</a> <button class="copy-btn" onclick="copyText('${vm.kamiUrl}', this)"><i class="fas fa-copy"></i></button></span></div>`;
    html += `</div><div class="info-section"><div class="info-section-title"><i class="fas fa-clock"></i> Timeline</div>
        <div class="info-row"><span class="info-label"><i class="far fa-calendar-plus"></i> Created</span><span class="info-value">${created}</span></div>
        <div class="info-row"><span class="info-label"><i class="far fa-calendar-times"></i> Expires</span><span class="info-value">${expires}</span></div></div>
        <div class="modal-actions">
            <button class="modal-btn" onclick="copyAllInfo('${vm.id}')"><i class="fas fa-copy"></i> Copy All</button>
            ${vm.repoUrl ? `<a href="${vm.repoUrl}" target="_blank" class="modal-btn"><i class="fab fa-github"></i> Repo</a>` : ''}
            <button class="modal-btn delete" onclick="deleteVMFromModal('${vm.id}')"><i class="fas fa-trash-alt"></i> Delete</button>
        </div>`;
    DOM.modalVmBody.innerHTML = html;
    DOM.vmModal.classList.add('show');
}

function closeVmModal() { DOM.vmModal.classList.remove('show'); }
async function copyText(text, btn) {
    try { await navigator.clipboard.writeText(text); btn.innerHTML = '<i class="fas fa-check"></i> Copied!'; setTimeout(() => btn.innerHTML = '<i class="fas fa-copy"></i>', 1500); }
    catch (e) { showToast('Copy failed', 'error'); }
}
function copyAllInfo(vmId) {
    const vm = vms.find(v => v.id === vmId);
    if (!vm) return;
    navigator.clipboard.writeText(`Natural VPS - ${vm.name}\nUser: ${vm.username}\nPass: ${vm.password}\nIP: ${vm.tailscaleIP || 'N/A'}\nKami: ${vm.kamiUrl || 'N/A'}`);
    showToast('Copied!', 'success');
    closeVmModal();
}
function deleteVMFromModal(vmId) { closeVmModal(); deleteVM(vmId); }
function selectOS(os) { selectedOS = os; document.querySelectorAll('.os-option').forEach(o => o.classList.remove('active')); document.querySelector(`.os-option[data-os="${os}"]`).classList.add('active'); }

function setupEventListeners() {
    document.querySelectorAll('.auth-tab').forEach(t => t.addEventListener('click', () => switchTab(t.dataset.tab)));
    DOM.loginForm.addEventListener('submit', async e => { e.preventDefault(); await login(DOM.loginUsername.value.trim(), DOM.loginPassword.value); });
    DOM.registerForm.addEventListener('submit', async e => { e.preventDefault(); await register(DOM.regUsername.value.trim(), DOM.regPassword.value); });
    DOM.logoutBtn.addEventListener('click', logout);
    DOM.createBtn.addEventListener('click', createVM);
    DOM.refreshBtn.addEventListener('click', () => { loadVMs(); loadStats(); loadRateLimit(); showToast('Refreshed', 'info'); });
    document.getElementById('randomUserBtn').addEventListener('click', () => DOM.vmUsername.value = generateUsername());
    document.getElementById('randomPassBtn').addEventListener('click', () => DOM.vmPassword.value = generatePassword());
    DOM.vmModal.addEventListener('click', e => { if (e.target.classList.contains('modal-overlay')) closeVmModal(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeVmModal(); });
}

async function init() {
    DOM.vmUsername.value = generateUsername();
    DOM.vmPassword.value = generatePassword();
    setupEventListeners();
    const loggedIn = await checkAuth();
    if (!loggedIn) DOM.authContainer.style.display = 'flex';
    setInterval(() => { if (currentUser) { loadVMs(); loadStats(); loadRateLimit(); } }, 30000);
}

document.addEventListener('DOMContentLoaded', init);
window.showVmModal = showVmModal;
window.closeVmModal = closeVmModal;
window.copyText = copyText;
window.copyAllInfo = copyAllInfo;
window.deleteVMFromModal = deleteVMFromModal;
window.selectOS = selectOS;
window.deleteVM = deleteVM;
