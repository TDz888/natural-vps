/* ============================================ */
/* NATURAL VPS - MAIN JAVASCRIPT                */
/* Cinematic Nature 4K - Chill Edition          */
/* Version: 2.0                                 */
/* ============================================ */

// ----- CONFIGURATION -----
const API_BASE = window.location.origin;

// ----- STATE -----
let currentUser = null;
let vms = [];
let selectedOS = 'ubuntu';
let progressInterval = null;
let currentCreatingVmId = null;
let countdownIntervals = {};

// ----- DOM ELEMENTS -----
const DOM = {
    // Auth
    authContainer: document.querySelector('.auth-container'),
    mainApp: document.querySelector('.main-app'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    loginUsername: document.getElementById('loginUsername'),
    loginPassword: document.getElementById('loginPassword'),
    rememberMe: document.getElementById('rememberMe'),
    regUsername: document.getElementById('regUsername'),
    regEmail: document.getElementById('regEmail'),
    regPassword: document.getElementById('regPassword'),
    regConfirmPassword: document.getElementById('regConfirmPassword'),
    
    // User menu
    userAvatar: document.getElementById('userAvatar'),
    userDisplayName: document.getElementById('userDisplayName'),
    logoutBtn: document.getElementById('logoutBtn'),
    
    // VM Form
    githubToken: document.getElementById('githubToken'),
    tailscaleKey: document.getElementById('tailscaleKey'),
    vmUsername: document.getElementById('vmUsername'),
    vmPassword: document.getElementById('vmPassword'),
    createBtn: document.getElementById('createBtn'),
    
    // VM List
    vmList: document.getElementById('vmList'),
    statTotal: document.getElementById('statTotal'),
    statRunning: document.getElementById('statRunning'),
    refreshBtn: document.getElementById('refreshBtn'),
    
    // Progress
    progressContainer: document.getElementById('createProgressContainer'),
    progressFill: document.getElementById('createProgressFill'),
    progressMessage: document.getElementById('createProgressMessage'),
    progressPercent: document.getElementById('createProgressPercent'),
    progressSteps: document.querySelectorAll('.progress-step'),
    
    // Modal
    vmModal: document.getElementById('vmModal'),
    modalVmName: document.getElementById('modalVmName'),
    modalVmBody: document.getElementById('modalVmBody')
};

// ============================================ */
// 🌿 NATURAL EFFECTS - INITIALIZATION           */
// ============================================ */

function initNaturalEffects() {
    createFogLayer();
    createCloudsLayer();
    createFallingLeaves();
    createFireflies();
    createSunraysLayer();
    startBirdAnimation();
    initRippleEffect();
    initParallaxEffect();
    initShootingStars();
}

function createFogLayer() {
    const fog = document.createElement('div');
    fog.className = 'fog-layer';
    document.body.appendChild(fog);
}

function createCloudsLayer() {
    const clouds = document.createElement('div');
    clouds.className = 'clouds-layer';
    clouds.innerHTML = `
        <div class="cloud cloud-1"></div>
        <div class="cloud cloud-2"></div>
        <div class="cloud cloud-3"></div>
    `;
    document.body.appendChild(clouds);
}

function createFallingLeaves() {
    const container = document.createElement('div');
    container.className = 'leaf-container';
    document.body.appendChild(container);
    
    const leafIcons = ['🍃', '🍂', '🌿', '🍁'];
    
    function spawnLeaf() {
        const leaf = document.createElement('div');
        leaf.className = 'falling-leaf';
        leaf.textContent = leafIcons[Math.floor(Math.random() * leafIcons.length)];
        leaf.style.left = Math.random() * 100 + '%';
        leaf.style.animationDuration = (8 + Math.random() * 10) + 's';
        leaf.style.animationDelay = Math.random() * 5 + 's';
        leaf.style.fontSize = (16 + Math.random() * 20) + 'px';
        container.appendChild(leaf);
        
        setTimeout(() => leaf.remove(), 20000);
    }
    
    for (let i = 0; i < 8; i++) {
        setTimeout(spawnLeaf, i * 300);
    }
    setInterval(spawnLeaf, 3000);
}

function createFireflies() {
    const container = document.createElement('div');
    container.className = 'firefly-container';
    document.body.appendChild(container);
    
    for (let i = 0; i < 20; i++) {
        const firefly = document.createElement('div');
        firefly.className = 'firefly';
        firefly.style.left = Math.random() * 100 + '%';
        firefly.style.top = Math.random() * 100 + '%';
        firefly.style.animationDelay = Math.random() * 3 + 's';
        firefly.style.animationDuration = (2 + Math.random() * 4) + 's';
        container.appendChild(firefly);
        
        animateFirefly(firefly);
    }
}

function animateFirefly(firefly) {
    function move() {
        const newX = parseFloat(firefly.style.left) + (Math.random() - 0.5) * 15;
        const newY = parseFloat(firefly.style.top) + (Math.random() - 0.5) * 15;
        
        firefly.style.left = Math.min(100, Math.max(0, newX)) + '%';
        firefly.style.top = Math.min(100, Math.max(0, newY)) + '%';
        firefly.style.transition = 'all ' + (3 + Math.random() * 5) + 's ease-in-out';
        
        setTimeout(move, 4000 + Math.random() * 6000);
    }
    move();
}

function createSunraysLayer() {
    const sunrays = document.createElement('div');
    sunrays.className = 'sunrays-layer';
    document.body.appendChild(sunrays);
}

function startBirdAnimation() {
    const container = document.createElement('div');
    container.className = 'bird-container';
    document.body.appendChild(container);
    
    function spawnBird() {
        const bird = document.createElement('div');
        bird.className = 'bird';
        bird.innerHTML = '🕊️';
        bird.style.top = (10 + Math.random() * 30) + '%';
        bird.style.animationDuration = (15 + Math.random() * 20) + 's';
        container.appendChild(bird);
        
        setTimeout(() => bird.remove(), 40000);
    }
    
    setInterval(spawnBird, 45000);
    setTimeout(spawnBird, 5000);
}

function initRippleEffect() {
    document.addEventListener('click', function(e) {
        const target = e.target.closest('.btn, .random-btn, .os-option, .vm-item, .modal-btn');
        if (!target) return;
        
        const ripple = document.createElement('span');
        ripple.className = 'ripple-effect';
        
        const rect = target.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
        
        target.appendChild(ripple);
        setTimeout(() => ripple.remove(), 800);
    });
}

function initParallaxEffect() {
    document.addEventListener('mousemove', function(e) {
        const moveX = (e.clientX - window.innerWidth / 2) / 50;
        const moveY = (e.clientY - window.innerHeight / 2) / 50;
        
        document.querySelectorAll('.spec-card, .card').forEach(el => {
            el.style.transform = `translate(${moveX * 0.2}px, ${moveY * 0.2}px)`;
        });
    });
}

function initShootingStars() {
    function createShootingStar() {
        const star = document.createElement('div');
        star.className = 'shooting-star';
        star.style.top = Math.random() * 30 + '%';
        star.style.left = Math.random() * 50 + 50 + '%';
        document.body.appendChild(star);
        
        setTimeout(() => star.classList.add('animate'), 100);
        setTimeout(() => star.remove(), 2000);
    }
    
    setInterval(() => {
        if (Math.random() > 0.7) {
            createShootingStar();
        }
    }, 8000);
}

// ============================================ */
// UTILITY FUNCTIONS                           */
// ============================================ */

function generateUsername() {
    const prefixes = ['forest', 'leaf', 'river', 'stone', 'wind', 'sun', 'moss', 'pine'];
    return prefixes[Math.floor(Math.random() * prefixes.length)] + '_' + 
           Math.random().toString(36).substring(2, 8);
}

function generatePassword(length = 14) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    return Array(length).fill(0).map(() => chars[Math.floor(Math.random() * chars.length)]).join('');
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

function getCountdownClass(expiresAt) {
    if (!expiresAt) return 'normal';
    const remaining = new Date(expiresAt) - Date.now();
    if (remaining <= 600000) return 'danger';
    if (remaining <= 3600000) return 'warning';
    return 'normal';
}

// ============================================ */
// TOAST NOTIFICATIONS                         */
// ============================================ */

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
        <i class="fas ${icons[type] || icons.info}"></i>
        <span class="toast-message">${message}</span>
        <span class="toast-close" onclick="this.parentElement.remove()">×</span>
    `;
    
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ============================================ */
// AUTHENTICATION                              */
// ============================================ */

async function register(username, password, email = null) {
    try {
        const confirmPassword = DOM.regConfirmPassword.value;
        
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
    } catch (e) {}
    
    currentUser = null;
    hideMainApp();
    showToast('Logged out successfully', 'info');
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

// ============================================ */
// VM MANAGEMENT                               */
// ============================================ */

async function loadVMs() {
    try {
        const res = await fetch(`${API_BASE}/api/vps`);
        const data = await res.json();
        
        if (data.success) {
            vms = data.vms || [];
            renderVMList(vms);
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
            DOM.statTotal.textContent = data.stats.total || 0;
            DOM.statRunning.textContent = data.stats.running || 0;
        }
    } catch (e) {
        console.error('Load stats error:', e);
    }
}

function renderVMList(vmArray) {
    if (!vmArray || vmArray.length === 0) {
        DOM.vmList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon"><i class="fas fa-seedling"></i></div>
                <p>Your virtual forest is empty</p>
                <small>Plant your first VM to begin</small>
            </div>
        `;
        return;
    }
    
    DOM.vmList.innerHTML = vmArray.map(vm => {
        const statusClass = vm.status === 'running' ? 'running' : 
                           (vm.status === 'creating' ? 'creating' : 'expired');
        
        return `
            <div class="vm-item" onclick="showVmModal('${vm.id}')">
                <div class="vm-header">
                    <div class="vm-info">
                        <div class="vm-icon">
                            <i class="fab fa-${vm.osType === 'ubuntu' ? 'ubuntu' : 'windows'}"></i>
                        </div>
                        <div>
                            <div class="vm-name">${vm.name || vm.id}</div>
                            <div class="vm-meta">
                                <span class="vm-status-dot ${statusClass}"></span>
                                <span class="vm-status-text">${vm.status}</span>
                                <span class="vm-time">• ${formatRelativeTime(vm.createdAt)}</span>
                            </div>
                        </div>
                    </div>
                    <i class="fas fa-chevron-right vm-arrow"></i>
                </div>
            </div>
        `;
    }).join('');
}

async function deleteVM(vmId) {
    if (!confirm('Are you sure you want to delete this VM?')) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/vps/${vmId}`, { method: 'DELETE' });
        const data = await res.json();
        
        if (data.success) {
            showToast('VM removed from your forest', 'success');
            if (countdownIntervals[vmId]) {
                clearInterval(countdownIntervals[vmId]);
                delete countdownIntervals[vmId];
            }
            loadVMs();
            loadStats();
        } else {
            showToast(data.error, 'error');
        }
    } catch (e) {
        showToast('Connection error', 'error');
    }
}

function selectOS(os) {
    selectedOS = os;
    document.querySelectorAll('.os-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector(`.os-option[data-os="${os}"]`).classList.add('active');
}

// ============================================ */
// PROGRESS TRACKING                           */
// ============================================ */

function updateProgressUI(step, percent, message) {
    DOM.progressFill.style.width = percent + '%';
    const msgSpan = DOM.progressMessage.querySelector('span') || DOM.progressMessage;
    if (msgSpan.tagName === 'SPAN') {
        msgSpan.textContent = message;
    } else {
        DOM.progressMessage.innerHTML = `<span>${message}</span>`;
    }
    DOM.progressPercent.textContent = percent + '%';
    
    DOM.progressSteps.forEach((s, index) => {
        s.classList.remove('active', 'completed');
        if (index < step) {
            s.classList.add('completed');
        } else if (index === step) {
            s.classList.add('active');
        }
    });
}

function startProgressTracking(vmId) {
    currentCreatingVmId = vmId;
    
    updateProgressUI(0, 5, '🔐 Validating token...');
    
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/vps/${vmId}/progress`);
            const data = await res.json();
            
            if (data.success) {
                const progress = data.progress;
                const vm = data.vm;
                
                updateProgressUI(progress.step, progress.percent, progress.message);
                
                if (progress.status === 'completed' || vm.status === 'running') {
                    clearInterval(progressInterval);
                    progressInterval = null;
                    currentCreatingVmId = null;
                    
                    loadVMs();
                    loadStats();
                    
                    setTimeout(() => {
                        DOM.progressContainer.style.display = 'none';
                    }, 3000);
                } else if (progress.status === 'failed') {
                    clearInterval(progressInterval);
                    progressInterval = null;
                    currentCreatingVmId = null;
                    
                    DOM.progressSteps[progress.step]?.classList.add('failed');
                    
                    setTimeout(() => {
                        DOM.progressContainer.style.display = 'none';
                    }, 5000);
                }
            }
        } catch (e) {
            console.error('Progress check error:', e);
        }
    }, 2000);
}

// ============================================ */
// CREATE VM                                   */
// ============================================ */

async function createVM() {
    const githubToken = DOM.githubToken.value.trim();
    const tailscaleKey = DOM.tailscaleKey.value.trim();
    let username = DOM.vmUsername.value.trim();
    let password = DOM.vmPassword.value;
    
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
        DOM.vmUsername.value = username;
    }
    
    if (!password) {
        password = generatePassword();
        DOM.vmPassword.value = password;
    }
    
    DOM.createBtn.disabled = true;
    DOM.createBtn.innerHTML = '<span class="spinner"></span> Planting...';
    
    DOM.progressContainer.style.display = 'block';
    updateProgressUI(0, 2, '🔐 Initializing...');
    
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
            
            DOM.githubToken.value = '';
            DOM.tailscaleKey.value = '';
            DOM.vmUsername.value = generateUsername();
            DOM.vmPassword.value = generatePassword();
            
            vms.unshift(data);
            renderVMList(vms);
            
            startProgressTracking(data.id);
        } else {
            showToast(data.error, 'error');
            DOM.progressContainer.style.display = 'none';
        }
    } catch (e) {
        showToast('Connection error', 'error');
        DOM.progressContainer.style.display = 'none';
    } finally {
        DOM.createBtn.disabled = false;
        DOM.createBtn.innerHTML = '<i class="fas fa-seedling"></i> Grow New VM';
    }
}

// ============================================ */
// VM MODAL                                    */
// ============================================ */

async function showVmModal(vmId) {
    const vm = vms.find(v => v.id === vmId);
    if (!vm) return;
    
    DOM.modalVmName.innerHTML = `<i class="fas fa-leaf"></i><span>${vm.name || vmId}</span>`;
    
    let isLive = false;
    try {
        const res = await fetch(`${API_BASE}/api/vps/${vmId}/check`);
        const data = await res.json();
        if (data.success) {
            isLive = data.is_live;
        }
    } catch (e) {}
    
    const created = new Date(vm.createdAt).toLocaleString();
    const expires = new Date(vm.expiresAt).toLocaleString();
    const remaining = formatCountdown(vm.expiresAt);
    const countdownClass = getCountdownClass(vm.expiresAt);
    
    let statusBadge = '';
    if (vm.status === 'creating') {
        statusBadge = '<span class="vm-status-badge creating"><i class="fas fa-spinner fa-pulse"></i> Creating</span>';
    } else if (isLive) {
        statusBadge = '<span class="vm-status-badge live"><i class="fas fa-circle"></i> Live</span>';
    } else {
        statusBadge = '<span class="vm-status-badge offline"><i class="fas fa-circle"></i> Offline</span>';
    }
    
    let html = `
        <div style="margin-bottom: 20px;">
            ${statusBadge}
            <span class="countdown-timer ${countdownClass}" style="margin-left: 10px;">
                <i class="fas fa-hourglass-half"></i> ${remaining}
            </span>
        </div>
        
        <div class="info-section">
            <div class="info-section-title"><i class="fas fa-info-circle"></i> General Information</div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-tag"></i> VM Name</span>
                <span class="info-value">${vm.name}</span>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-microchip"></i> Operating System</span>
                <span class="info-value">
                    <i class="fab fa-${vm.osType === 'ubuntu' ? 'ubuntu' : 'windows'}" style="color: ${vm.osType === 'ubuntu' ? '#dd4814' : '#00a4ef'};"></i>
                    ${vm.osType === 'ubuntu' ? 'Ubuntu 22.04 LTS' : 'Windows Server 2022'}
                </span>
            </div>
        </div>
        
        <div class="info-section">
            <div class="info-section-title"><i class="fas fa-key"></i> Credentials</div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-user"></i> Username</span>
                <span class="info-value">
                    ${vm.username}
                    <button class="copy-btn" onclick="copyText('${vm.username}', this)"><i class="fas fa-copy"></i></button>
                </span>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-lock"></i> Password</span>
                <span class="info-value">
                    ${vm.password}
                    <button class="copy-btn" onclick="copyText('${vm.password}', this)"><i class="fas fa-copy"></i></button>
                </span>
            </div>
        </div>
        
        <div class="info-section">
            <div class="info-section-title"><i class="fas fa-network-wired"></i> Connection</div>
    `;
    
    if (vm.osType === 'ubuntu' && vm.sshCommand) {
        html += `
            <div class="info-row">
                <span class="info-label"><i class="fas fa-terminal"></i> SSH Command</span>
                <span class="info-value">
                    ${vm.sshCommand}
                    <button class="copy-btn" onclick="copyText('${vm.sshCommand}', this)"><i class="fas fa-copy"></i></button>
                </span>
            </div>
        `;
    }
    
    if (vm.tailscaleIP) {
        html += `
            <div class="info-row">
                <span class="info-label"><i class="fas fa-ip"></i> Tailscale IP</span>
                <span class="info-value">
                    ${vm.tailscaleIP}
                    <button class="copy-btn" onclick="copyText('${vm.tailscaleIP}', this)"><i class="fas fa-copy"></i></button>
                </span>
            </div>
        `;
    }
    
    if (vm.cloudflareUrl) {
        html += `
            <div class="info-row">
                <span class="info-label"><i class="fas fa-cloud"></i> Cloudflare VNC</span>
                <span class="info-value">
                    <a href="${vm.cloudflareUrl}" target="_blank" style="color: var(--green-moss);">Open VNC</a>
                    <button class="copy-btn" onclick="copyText('${vm.cloudflareUrl}', this)"><i class="fas fa-copy"></i></button>
                </span>
            </div>
        `;
    }
    
    html += `
        </div>
        
        <div class="info-section">
            <div class="info-section-title"><i class="fas fa-clock"></i> Timeline</div>
            <div class="info-row">
                <span class="info-label"><i class="far fa-calendar-plus"></i> Created</span>
                <span class="info-value">${created}</span>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="far fa-calendar-times"></i> Expires</span>
                <span class="info-value">${expires}</span>
            </div>
        </div>
        
        <div class="modal-actions">
            <button class="modal-btn" onclick="copyAllInfo('${vm.id}')">
                <i class="fas fa-copy"></i> Copy All
            </button>
            ${vm.repoUrl ? `
                <a href="${vm.repoUrl}" target="_blank" class="modal-btn">
                    <i class="fab fa-github"></i> Repository
                </a>
            ` : ''}
            <button class="modal-btn delete" onclick="deleteVMFromModal('${vm.id}')">
                <i class="fas fa-trash-alt"></i> Delete
            </button>
        </div>
    `;
    
    DOM.modalVmBody.innerHTML = html;
    DOM.vmModal.classList.add('show');
}

function closeVmModal() {
    DOM.vmModal.classList.remove('show');
}

async function copyText(text, btn) {
    try {
        await navigator.clipboard.writeText(text);
        const original = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.innerHTML = original;
            btn.classList.remove('copied');
        }, 1500);
    } catch (e) {
        showToast('Copy failed', 'error');
    }
}

function copyAllInfo(vmId) {
    const vm = vms.find(v => v.id === vmId);
    if (!vm) return;
    
    const info = `
Natural VPS - ${vm.name}
========================
OS: ${vm.osType === 'ubuntu' ? 'Ubuntu 22.04' : 'Windows Server'}
Username: ${vm.username}
Password: ${vm.password}
Tailscale IP: ${vm.tailscaleIP || 'N/A'}
${vm.osType === 'ubuntu' ? `SSH: ${vm.sshCommand || 'N/A'}` : `VNC: ${vm.cloudflareUrl || 'N/A'}`}
Repository: ${vm.repoUrl || 'N/A'}
Created: ${vm.createdAt}
Expires: ${vm.expiresAt}
Status: ${vm.status}
    `.trim();
    
    navigator.clipboard.writeText(info);
    showToast('✅ All information copied!', 'success');
    closeVmModal();
}

function deleteVMFromModal(vmId) {
    closeVmModal();
    deleteVM(vmId);
}

// ============================================ */
// EVENT LISTENERS                             */
// ============================================ */

function setupEventListeners() {
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    DOM.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await login(DOM.loginUsername.value.trim(), DOM.loginPassword.value, DOM.rememberMe.checked);
    });
    
    DOM.registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await register(
            DOM.regUsername.value.trim(),
            DOM.regPassword.value,
            DOM.regEmail.value.trim() || null
        );
    });
    
    DOM.logoutBtn.addEventListener('click', logout);
    DOM.createBtn.addEventListener('click', createVM);
    
    DOM.refreshBtn.addEventListener('click', () => {
        loadVMs();
        loadStats();
        showToast('Forest refreshed', 'info');
    });
    
    document.getElementById('randomUserBtn').addEventListener('click', () => {
        DOM.vmUsername.value = generateUsername();
    });
    
    document.getElementById('randomPassBtn').addEventListener('click', () => {
        DOM.vmPassword.value = generatePassword();
    });
    
    DOM.vmModal.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            closeVmModal();
        }
    });
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeVmModal();
        }
    });
}

// ============================================ */
// INITIALIZATION                              */
// ============================================ */

async function init() {
    initNaturalEffects();
    
    DOM.vmUsername.value = generateUsername();
    DOM.vmPassword.value = generatePassword();
    
    setupEventListeners();
    
    const isLoggedIn = await checkAuth();
    
    if (!isLoggedIn) {
        DOM.authContainer.style.display = 'flex';
    }
    
    setInterval(() => {
        if (currentUser) {
            loadVMs();
            loadStats();
        }
    }, 30000);
}

document.addEventListener('DOMContentLoaded', init);

window.showVmModal = showVmModal;
window.closeVmModal = closeVmModal;
window.copyText = copyText;
window.copyAllInfo = copyAllInfo;
window.deleteVMFromModal = deleteVMFromModal;
window.selectOS = selectOS;
window.deleteVM = deleteVM;
