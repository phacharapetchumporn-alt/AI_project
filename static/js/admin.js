/**
 * SignSubs Admin Backoffice - Client Logic
 * Handles interactive dashboard analytics, user CRUD, gesture vocab management,
 * translation logs, audit logs, and system settings.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State Store
    const state = {
        currentView: 'overview',
        users: [],
        gestures: [],
        translations: [],
        logs: [],
        settings: {},
        chartInstance: null
    };

    // DOM Elements
    const sidebar = document.getElementById('admin-sidebar');
    const btnMobileMenu = document.getElementById('btn-mobile-menu');
    const navButtons = document.querySelectorAll('.nav-item-btn[data-view]');
    const viewPanes = document.querySelectorAll('.admin-view-pane');
    const pageTitle = document.getElementById('page-title');
    const btnRefresh = document.getElementById('btn-refresh-data');
    const toastContainer = document.getElementById('toast-container');

    // ==========================================================================
    // Toast Notification System
    // ==========================================================================
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation';
        toast.innerHTML = `
            <i class="fa-solid ${icon}" style="font-size: 1.1rem; color: ${type === 'success' ? 'var(--accent-green)' : 'var(--accent-red)'}"></i>
            <span>${message}</span>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // ==========================================================================
    // View Switcher & Mobile Menu
    // ==========================================================================
    const VIEW_TITLES = {
        overview: '<i class="fa-solid fa-chart-pie"></i> ภาพรวมระบบ (Dashboard Overview)',
        users: '<i class="fa-solid fa-users-gear"></i> จัดการผู้ใช้งาน (User Management)',
        gestures: '<i class="fa-solid fa-hands-asl-interpreting"></i> คลังคำศัพท์ภาษามือ (Gesture Vocabulary)',
        translations: '<i class="fa-solid fa-clock-rotate-left"></i> ประวัติการแปล AI (Translation History)',
        logs: '<i class="fa-solid fa-shield-virus"></i> บันทึกกิจกรรมระบบ (System Audit Logs)',
        settings: '<i class="fa-solid fa-sliders"></i> ตั้งค่าระบบและโมเดล AI (System Settings)'
    };

    window.adminSwitchView = function (viewName) {
        if (!viewName) return;
        state.currentView = viewName;

        // Update nav items
        navButtons.forEach(btn => {
            if (btn.getAttribute('data-view') === viewName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update view panes
        viewPanes.forEach(pane => {
            if (pane.id === `view-${viewName}`) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });

        // Update Title
        if (pageTitle && VIEW_TITLES[viewName]) {
            pageTitle.innerHTML = VIEW_TITLES[viewName];
        }

        // Close mobile drawer if open
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }

        // Load data for view
        if (viewName === 'overview') loadOverviewStats();
        else if (viewName === 'users') loadUsers();
        else if (viewName === 'gestures') loadGestures();
        else if (viewName === 'translations') loadTranslations();
        else if (viewName === 'logs') loadLogs();
        else if (viewName === 'settings') loadSettings();
    };

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetView = btn.getAttribute('data-view');
            window.adminSwitchView(targetView);
        });
    });

    if (btnMobileMenu) {
        btnMobileMenu.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    if (btnRefresh) {
        btnRefresh.addEventListener('click', () => {
            window.adminSwitchView(state.currentView);
            showToast('รีเฟรชข้อมูลเรียบร้อยแล้ว');
        });
    }

    // ==========================================================================
    // 1. OVERVIEW DASHBOARD
    // ==========================================================================
    async function loadOverviewStats() {
        try {
            const res = await fetch('/api/admin/stats');
            if (!res.ok) throw new Error('Cannot fetch stats');
            const data = await res.json();

            // Populate cards
            document.getElementById('stat-total-users').textContent = data.total_users || 0;
            document.getElementById('stat-active-users').textContent = `ผู้ดูแล ${data.total_admins || 1} คน / ใช้งานล่าสุด ${data.active_users || 0} คน`;
            document.getElementById('sidebar-user-count').textContent = data.total_users || 0;

            document.getElementById('stat-total-translations').textContent = data.total_translations || 0;
            document.getElementById('stat-avg-confidence').textContent = `ความแม่นยำเฉลี่ย ${data.avg_confidence || 97.5}%`;

            document.getElementById('stat-total-gestures').textContent = data.total_gestures || 0;
            document.getElementById('sidebar-gesture-count').textContent = data.total_gestures || 0;
            document.getElementById('stat-active-gestures').textContent = `เปิดใช้งาน ${data.active_gestures || 0} ท่าทาง`;

            // AI Status
            if (data.ai_engine) {
                document.getElementById('stat-ai-status').textContent = 'Online';
                document.getElementById('stat-ai-device').textContent = `${data.ai_engine.device || 'CPU'} | Ready`;
                document.getElementById('ai-engine-status-text').textContent = 'Bi-LSTM Ready';
            }

            // Specs
            if (data.system) {
                document.getElementById('spec-python').textContent = data.system.python_version || 'Python 3.x';
                document.getElementById('spec-lan-ip').textContent = data.system.lan_ip ? `${data.system.lan_ip}:${data.system.port || 5000}` : 'localhost:5000';
                document.getElementById('spec-ssl').textContent = data.system.is_ssl ? 'Active (HTTPS)' : 'HTTP (Local)';
                document.getElementById('spec-ssl').style.color = data.system.is_ssl ? 'var(--accent-green)' : 'var(--accent-yellow)';
            }

            // Render Recent Translations Table
            renderOverviewRecent(data.recent_translations || []);

            // Render Chart
            renderWeeklyChart(data.weekly_stats || []);

            // Current admin info
            if (data.current_user) {
                document.getElementById('sidebar-admin-name').textContent = data.current_user.username || 'Admin';
                const initials = (data.current_user.username || 'AD').substring(0, 2).toUpperCase();
                document.getElementById('sidebar-admin-avatar').textContent = initials;
            }

        } catch (err) {
            console.error('Error loading overview stats:', err);
        }
    }

    function renderOverviewRecent(items) {
        const tbody = document.getElementById('overview-recent-translations');
        if (!tbody) return;

        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-tertiary); padding: 24px;">ยังไม่มีประวัติการแปล</td></tr>`;
            return;
        }

        tbody.innerHTML = items.map(item => `
            <tr>
                <td><span style="font-weight: 500;">${item.username || 'Guest'}</span></td>
                <td><code style="color: var(--accent-cyan); background: rgba(6,182,212,0.1); padding: 2px 6px; border-radius: 4px;">${item.gesture_name}</code></td>
                <td><strong style="color: #fff;">${item.translation_text}</strong></td>
                <td>
                    <span class="confidence-pill" style="color: ${item.confidence >= 90 ? 'var(--accent-green)' : 'var(--accent-yellow)'}">
                        <span class="confidence-dot" style="background: ${item.confidence >= 90 ? 'var(--accent-green)' : 'var(--accent-yellow)'}"></span>
                        ${item.confidence}%
                    </span>
                </td>
                <td style="color: var(--text-tertiary); font-size: 0.82rem;">${item.timestamp}</td>
            </tr>
        `).join('');
    }

    function renderWeeklyChart(weeklyData) {
        const canvas = document.getElementById('chart-translations');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (state.chartInstance) {
            state.chartInstance.destroy();
        }

        const labels = weeklyData.map(d => d.date);
        const counts = weeklyData.map(d => d.count);

        state.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.length ? labels : ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัส', 'ศุกร์', 'เสาร์', 'อาทิตย์'],
                datasets: [{
                    label: 'จำนวนครั้งที่แปลสำเร็จ',
                    data: counts.length ? counts : [12, 19, 15, 27, 34, 42, 38],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#818cf8',
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8', stepSize: 5 },
                        beginAtZero: true
                    }
                }
            }
        });
    }
    // ==========================================================================
    // SUPABASE GLOBAL INITIALIZATION
    // ==========================================================================
    const SUPABASE_URL = 'https://yotvhpskwnmhupvaxenf.supabase.co';
    const SUPABASE_ANON_KEY = 'sb_publishable_z8cNBJEv-QhG8ULD8yg63A_RdZeaXGa';

    // สร้าง client ทันทีโดยอ้างอิงจาก window.supabase
    let supabaseClient = null;
    if (window.supabase && typeof window.supabase.createClient === 'function') {
        supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    }

    // ==========================================================================
    // 2. USER MANAGEMENT
    // ==========================================================================
    const usersTableBody = document.getElementById('users-table-body');
    const usersSearchInput = document.getElementById('users-search-input');
    const usersFilterRole = document.getElementById('users-filter-role');
    const usersFilterStatus = document.getElementById('users-filter-status');
    const modalUser = document.getElementById('modal-user');
    const btnAddUser = document.getElementById('btn-add-user');
    const btnCloseUserModal = document.getElementById('btn-close-user-modal');
    const btnCancelUserModal = document.getElementById('btn-cancel-user-modal');
    const formUserSave = document.getElementById('form-user-save');

    async function loadUsers() {
        try {
            // 1. ดึงข้อมูลผู้ใช้ทั้งหมดจากตาราง users ใน Supabase เรียงจากล่าสุดไปเก่าสุด
            const { data: users, error } = await supabaseClient
                .from('users')
                .select('*')

            if (error) {
                console.error("Error fetching users:", error);
                throw new Error('Cannot fetch users from Supabase');
            }

            // 2. เก็บข้อมูลลงใน state ของระบบหน้าแอดมิน
            state.users = users || [];

            // 3. เรียกฟังก์ชันวาดตารางเดิมที่มีอยู่แล้วในระบบ
            renderUsersTable();

        } catch (err) {
            console.error(err);
            showToast('เกิดข้อผิดพลาดในการโหลดรายชื่อผู้ใช้', 'error');
        }
    }

    // เรียกใช้งานฟังก์ชันเมื่อหน้าเว็บโหลดเสร็จ
    document.addEventListener('DOMContentLoaded', () => {
        loadUsers();
    });

    function renderUsersTable() {
        if (!usersTableBody) return;
        const query = usersSearchInput ? usersSearchInput.value.toLowerCase().trim() : '';
        const roleFilter = usersFilterRole ? usersFilterRole.value : '';
        const statusFilter = usersFilterStatus ? usersFilterStatus.value : '';

        const filtered = state.users.filter(u => {
            const matchQuery = !query || u.username.toLowerCase().includes(query) || u.email.toLowerCase().includes(query);
            const matchRole = !roleFilter || u.role === roleFilter;
            const matchStatus = !statusFilter || (u.status || 'active') === statusFilter;
            return matchQuery && matchRole && matchStatus;
        });

        if (filtered.length === 0) {
            usersTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-tertiary); padding: 32px;">ไม่พบข้อมูลผู้ใช้งานที่ตรงกับเงื่อนไข</td></tr>`;
            return;
        }

        usersTableBody.innerHTML = filtered.map(u => {
            const initials = u.username.substring(0, 2).toUpperCase();
            const isAdmin = u.role === 'admin';
            const isBanned = u.status === 'banned';

            return `
                <tr>
                    <td>
                        <div class="user-table-cell">
                            <div class="user-mini-avatar" style="${isAdmin ? 'background: linear-gradient(135deg, var(--accent-purple), var(--primary));' : ''}">${initials}</div>
                            <div>
                                <strong style="color: #fff; font-size: 0.92rem;">${u.username}</strong>
                                <div style="font-size: 0.75rem; color: var(--text-tertiary);">ID #${u.id}</div>
                            </div>
                        </div>
                    </td>
                    <td>${u.email}</td>
                    <td>
                        <span class="badge-tag ${isAdmin ? 'badge-admin' : 'badge-user'}">
                            <i class="fa-solid ${isAdmin ? 'fa-crown' : 'fa-user'}"></i>
                            ${isAdmin ? 'Admin' : 'Member'}
                        </span>
                    </td>
                    <td>
                        <span class="badge-tag ${isBanned ? 'badge-banned' : 'badge-active'}">
                            <i class="fa-solid ${isBanned ? 'fa-ban' : 'fa-circle-check'}"></i>
                            ${isBanned ? 'Banned' : 'Active'}
                        </span>
                    </td>
                    <td style="color: var(--text-tertiary); font-size: 0.82rem;">${u.created_at || '-'}</td>
                    <td style="text-align: right;">
                        <div class="action-btn-group" style="justify-content: flex-end;">
                            <button class="btn-icon-action" onclick="openEditUserModal(${u.id})" title="แก้ไขข้อมูล">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn-icon-action danger" onclick="deleteUser(${u.id}, '${u.username}')" title="ลบผู้ใช้">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    if (usersSearchInput) usersSearchInput.addEventListener('input', renderUsersTable);
    if (usersFilterRole) usersFilterRole.addEventListener('change', renderUsersTable);
    if (usersFilterStatus) usersFilterStatus.addEventListener('change', renderUsersTable);

    if (btnAddUser) {
        btnAddUser.addEventListener('click', () => {
            document.getElementById('modal-user-title').innerHTML = '<i class="fa-solid fa-user-plus"></i> เพิ่มผู้ใช้งานใหม่';
            document.getElementById('user-form-id').value = '';
            document.getElementById('user-form-username').value = '';
            document.getElementById('user-form-username').disabled = false;
            document.getElementById('user-form-email').value = '';
            document.getElementById('user-form-password').value = '';
            document.getElementById('user-form-password').required = true;
            document.getElementById('user-password-hint').style.display = 'none';
            document.getElementById('user-form-role').value = 'user';
            document.getElementById('user-form-status').value = 'active';
            modalUser.classList.add('active');
        });
    }

    window.openEditUserModal = function (userId) {
        const user = state.users.find(u => u.id === userId);
        if (!user) return;

        document.getElementById('modal-user-title').innerHTML = `<i class="fa-solid fa-user-pen"></i> แก้ไขผู้ใช้: ${user.username}`;
        document.getElementById('user-form-id').value = user.id;
        document.getElementById('user-form-username').value = user.username;
        document.getElementById('user-form-username').disabled = true;
        document.getElementById('user-form-email').value = user.email;
        document.getElementById('user-form-password').value = '';
        document.getElementById('user-form-password').required = false;
        document.getElementById('user-password-hint').style.display = 'block';
        document.getElementById('user-form-role').value = user.role || 'user';
        document.getElementById('user-form-status').value = user.status || 'active';
        modalUser.classList.add('active');
    };

    function closeUserModal() {
        modalUser.classList.remove('active');
    }
    if (btnCloseUserModal) btnCloseUserModal.addEventListener('click', closeUserModal);
    if (btnCancelUserModal) btnCancelUserModal.addEventListener('click', closeUserModal);

    if (formUserSave) {
        formUserSave.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('user-form-id').value;
            const username = document.getElementById('user-form-username').value.trim();
            const email = document.getElementById('user-form-email').value.trim();
            const password = document.getElementById('user-form-password').value;
            const role = document.getElementById('user-form-role').value;
            const status = document.getElementById('user-form-status').value;

            try {
                if (id) {
                    // Update user
                    const payload = { email, role, status };
                    if (password) payload.password = password;

                    const res = await fetch(`/api/admin/users/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.message || 'Error updating user');
                    showToast('อัปเดตข้อมูลผู้ใช้สำเร็จ');
                } else {
                    // Create user
                    const res = await fetch('/api/admin/users', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, email, password, role, status })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.message || 'Error adding user');
                    showToast(`เพิ่มผู้ใช้งาน ${username} สำเร็จ`);
                }
                closeUserModal();
                loadUsers();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    window.deleteUser = async function (userId, username) {
        if (!confirm(`คุณต้องการลบผู้ใช้ "${username}" ใช่หรือไม่? การกระทำนี้ไม่สามารถย้อนกลับได้`)) return;

        try {
            const res = await fetch(`/api/admin/users/${userId}`, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.message || 'Error deleting user');
            showToast(`ลบผู้ใช้ "${username}" เรียบร้อย`);
            loadUsers();
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    // ==========================================================================
    // 3. GESTURE VOCABULARY MANAGEMENT
    // ==========================================================================
    const gesturesTableBody = document.getElementById('gestures-table-body');
    const gesturesSearchInput = document.getElementById('gestures-search-input');
    const gesturesFilterCategory = document.getElementById('gestures-filter-category');
    const modalGesture = document.getElementById('modal-gesture');
    const btnAddGesture = document.getElementById('btn-add-gesture');
    const btnCloseGestureModal = document.getElementById('btn-close-gesture-modal');
    const btnCancelGestureModal = document.getElementById('btn-cancel-gesture-modal');
    const formGestureSave = document.getElementById('form-gesture-save');

    async function loadGestures() {
        try {
            const res = await fetch('/api/admin/gestures');
            if (!res.ok) throw new Error('Cannot fetch gestures');
            state.gestures = await res.json();
            renderGesturesTable();
        } catch (err) {
            console.error(err);
            showToast('เกิดข้อผิดพลาดในการโหลดคำศัพท์ภาษามือ', 'error');
        }
    }

    function renderGesturesTable() {
        if (!gesturesTableBody) return;
        const query = gesturesSearchInput ? gesturesSearchInput.value.toLowerCase().trim() : '';
        const catFilter = gesturesFilterCategory ? gesturesFilterCategory.value : '';

        const filtered = state.gestures.filter(g => {
            const matchQuery = !query ||
                g.gesture_key.toLowerCase().includes(query) ||
                g.name_th.toLowerCase().includes(query) ||
                g.name_en.toLowerCase().includes(query);
            const matchCat = !catFilter || g.category === catFilter;
            return matchQuery && matchCat;
        });

        if (filtered.length === 0) {
            gesturesTableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-tertiary); padding: 32px;">ไม่พบคำศัพท์ภาษามือที่ตรงกับเงื่อนไข</td></tr>`;
            return;
        }

        gesturesTableBody.innerHTML = filtered.map(g => {
            const isActive = g.is_active === 1;

            return `
                <tr>
                    <td><code style="color: var(--accent-cyan); font-weight: 700; background: rgba(6,182,212,0.1); padding: 3px 8px; border-radius: 6px;">${g.gesture_key}</code></td>
                    <td><strong style="color: #fff; font-size: 0.95rem;">${g.name_th}</strong></td>
                    <td style="color: var(--text-secondary);">${g.name_en}</td>
                    <td><span class="badge-tag badge-category">${g.category || 'ทั่วไป'}</span></td>
                    <td>
                        <span style="font-size: 0.8rem; color: ${g.difficulty === 'ง่าย' ? 'var(--accent-green)' : g.difficulty === 'ปานกลาง' ? 'var(--accent-yellow)' : 'var(--accent-red)'}">
                            ${g.difficulty || 'ง่าย'}
                        </span>
                    </td>
                    <td style="font-family: monospace; color: var(--text-secondary);">${g.sample_count || 100} เฟรม</td>
                    <td>
                        <span class="badge-tag ${isActive ? 'badge-active' : 'badge-banned'}">
                            <i class="fa-solid ${isActive ? 'fa-check' : 'fa-pause'}"></i>
                            ${isActive ? 'พร้อมตรวจจับ' : 'ปิดใช้งาน'}
                        </span>
                    </td>
                    <td style="text-align: right;">
                        <div class="action-btn-group" style="justify-content: flex-end;">
                            <button class="btn-icon-action" onclick="openEditGestureModal(${g.id})" title="แก้ไขคำศัพท์">
                                <i class="fa-solid fa-pen-to-square"></i>
                            </button>
                            <button class="btn-icon-action danger" onclick="deleteGesture(${g.id}, '${g.name_th}')" title="ลบคำศัพท์">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    if (gesturesSearchInput) gesturesSearchInput.addEventListener('input', renderGesturesTable);
    if (gesturesFilterCategory) gesturesFilterCategory.addEventListener('change', renderGesturesTable);

    if (btnAddGesture) {
        btnAddGesture.addEventListener('click', () => {
            document.getElementById('modal-gesture-title').innerHTML = '<i class="fa-solid fa-plus"></i> เพิ่มคำศัพท์ภาษามือ';
            document.getElementById('gesture-form-id').value = '';
            document.getElementById('gesture-form-key').value = '';
            document.getElementById('gesture-form-key').disabled = false;
            document.getElementById('gesture-form-name-th').value = '';
            document.getElementById('gesture-form-name-en').value = '';
            document.getElementById('gesture-form-category').value = 'ตัวเลข';
            document.getElementById('gesture-form-difficulty').value = 'ง่าย';
            document.getElementById('gesture-form-desc').value = '';
            document.getElementById('gesture-form-status').value = '1';
            modalGesture.classList.add('active');
        });
    }

    window.openEditGestureModal = function (id) {
        const item = state.gestures.find(g => g.id === id);
        if (!item) return;

        document.getElementById('modal-gesture-title').innerHTML = `<i class="fa-solid fa-pen-to-square"></i> แก้ไขคำศัพท์: ${item.name_th}`;
        document.getElementById('gesture-form-id').value = item.id;
        document.getElementById('gesture-form-key').value = item.gesture_key;
        document.getElementById('gesture-form-key').disabled = true;
        document.getElementById('gesture-form-name-th').value = item.name_th;
        document.getElementById('gesture-form-name-en').value = item.name_en;
        document.getElementById('gesture-form-category').value = item.category || 'ทั่วไป';
        document.getElementById('gesture-form-difficulty').value = item.difficulty || 'ง่าย';
        document.getElementById('gesture-form-desc').value = item.description || '';
        document.getElementById('gesture-form-status').value = String(item.is_active);
        modalGesture.classList.add('active');
    };

    function closeGestureModal() {
        modalGesture.classList.remove('active');
    }
    if (btnCloseGestureModal) btnCloseGestureModal.addEventListener('click', closeGestureModal);
    if (btnCancelGestureModal) btnCancelGestureModal.addEventListener('click', closeGestureModal);

    if (formGestureSave) {
        formGestureSave.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('gesture-form-id').value;
            const gesture_key = document.getElementById('gesture-form-key').value.trim();
            const name_th = document.getElementById('gesture-form-name-th').value.trim();
            const name_en = document.getElementById('gesture-form-name-en').value.trim();
            const category = document.getElementById('gesture-form-category').value;
            const difficulty = document.getElementById('gesture-form-difficulty').value;
            const description = document.getElementById('gesture-form-desc').value.trim();
            const is_active = parseInt(document.getElementById('gesture-form-status').value, 10);

            try {
                if (id) {
                    const res = await fetch(`/api/admin/gestures/${id}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name_th, name_en, category, difficulty, description, is_active })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.message || 'Error updating gesture');
                    showToast('อัปเดตคำศัพท์ภาษามือสำเร็จ');
                } else {
                    const res = await fetch('/api/admin/gestures', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ gesture_key, name_th, name_en, category, difficulty, description, is_active })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.message || 'Error adding gesture');
                    showToast(`เพิ่มคำศัพท์ "${name_th}" สำเร็จ`);
                }
                closeGestureModal();
                loadGestures();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    window.deleteGesture = async function (id, name) {
        if (!confirm(`คุณต้องการลบคำศัพท์ "${name}" ออกจากคลังใช่หรือไม่?`)) return;

        try {
            const res = await fetch(`/api/admin/gestures/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.message || 'Error deleting gesture');
            showToast(`ลบคำศัพท์ "${name}" เรียบร้อย`);
            loadGestures();
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    // ==========================================================================
    // 4. TRANSLATION HISTORY
    // ==========================================================================
    const translationsTableBody = document.getElementById('translations-table-body');
    const translationsSearchInput = document.getElementById('translations-search-input');
    const btnClearTranslations = document.getElementById('btn-clear-translations');
    const btnExportTranslations = document.getElementById('btn-export-translations');

    async function loadTranslations() {
        try {
            const res = await fetch('/api/admin/translations');
            if (!res.ok) throw new Error('Cannot fetch translations');
            state.translations = await res.json();
            renderTranslationsTable();
        } catch (err) {
            console.error(err);
            showToast('เกิดข้อผิดพลาดในการโหลดประวัติการแปล', 'error');
        }
    }

    function renderTranslationsTable() {
        if (!translationsTableBody) return;
        const query = translationsSearchInput ? translationsSearchInput.value.toLowerCase().trim() : '';

        const filtered = state.translations.filter(t => {
            return !query ||
                (t.username || '').toLowerCase().includes(query) ||
                (t.gesture_name || '').toLowerCase().includes(query) ||
                (t.translation_text || '').toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            translationsTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-tertiary); padding: 32px;">ไม่พบประวัติการแปล</td></tr>`;
            return;
        }

        translationsTableBody.innerHTML = filtered.map((t, idx) => `
            <tr>
                <td style="color: var(--text-tertiary); font-size: 0.82rem;">#${t.id || (idx + 1)}</td>
                <td><strong style="color: #fff;">${t.username || 'Guest'}</strong></td>
                <td><code style="color: var(--accent-cyan); background: rgba(6,182,212,0.1); padding: 2px 6px; border-radius: 4px;">${t.gesture_name}</code></td>
                <td><span style="font-size: 0.95rem; font-weight: 600; color: #fff;">${t.translation_text}</span></td>
                <td>
                    <span class="confidence-pill" style="color: ${t.confidence >= 90 ? 'var(--accent-green)' : 'var(--accent-yellow)'}">
                        <span class="confidence-dot" style="background: ${t.confidence >= 90 ? 'var(--accent-green)' : 'var(--accent-yellow)'}"></span>
                        ${t.confidence}%
                    </span>
                </td>
                <td style="color: var(--text-tertiary); font-size: 0.82rem;">${t.timestamp}</td>
                <td style="text-align: right;">
                    <button class="btn-icon-action danger" onclick="deleteTranslationLog(${t.id})" title="ลบรายการนี้">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    if (translationsSearchInput) translationsSearchInput.addEventListener('input', renderTranslationsTable);

    window.deleteTranslationLog = async function (id) {
        try {
            const res = await fetch(`/api/admin/translations/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error('Error deleting log');
            showToast('ลบรายการประวัติสำเร็จ');
            loadTranslations();
        } catch (err) {
            showToast(err.message, 'error');
        }
    };

    if (btnClearTranslations) {
        btnClearTranslations.addEventListener('click', async () => {
            if (!confirm('คุณแน่ใจหรือไม่ว่าต้องการล้างประวัติการแปลทั้งหมด? ข้อมูลจะไม่สามารถกู้คืนได้')) return;

            try {
                const res = await fetch('/api/admin/translations/clear', { method: 'POST' });
                if (!res.ok) throw new Error('Error clearing translations');
                showToast('ล้างประวัติการแปลทั้งหมดเรียบร้อยแล้ว');
                loadTranslations();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    if (btnExportTranslations) {
        btnExportTranslations.addEventListener('click', () => {
            window.location.href = '/api/admin/export/translations';
        });
    }

    // ==========================================================================
    // 5. SYSTEM & AUDIT LOGS
    // ==========================================================================
    const logsTableBody = document.getElementById('logs-table-body');
    const logsSearchInput = document.getElementById('logs-search-input');
    const btnClearLogs = document.getElementById('btn-clear-logs');

    async function loadLogs() {
        try {
            const res = await fetch('/api/admin/logs');
            if (!res.ok) throw new Error('Cannot fetch logs');
            state.logs = await res.json();
            renderLogsTable();
        } catch (err) {
            console.error(err);
            showToast('เกิดข้อผิดพลาดในการโหลดบันทึกกิจกรรม', 'error');
        }
    }

    function renderLogsTable() {
        if (!logsTableBody) return;
        const query = logsSearchInput ? logsSearchInput.value.toLowerCase().trim() : '';

        const filtered = state.logs.filter(l => {
            return !query ||
                l.action.toLowerCase().includes(query) ||
                (l.actor || '').toLowerCase().includes(query) ||
                (l.details || '').toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            logsTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-tertiary); padding: 32px;">ไม่พบบันทึกกิจกรรม</td></tr>`;
            return;
        }

        logsTableBody.innerHTML = filtered.map(l => `
            <tr>
                <td style="color: var(--text-tertiary); font-size: 0.82rem; white-space: nowrap;">${l.created_at}</td>
                <td>
                    <span class="badge-tag" style="background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3);">
                        <i class="fa-solid fa-clock-rotate-left"></i> ${l.action}
                    </span>
                </td>
                <td><strong style="color: #fff;">${l.actor || 'System'}</strong></td>
                <td><code style="color: var(--text-tertiary); font-size: 0.8rem;">${l.ip_address || '127.0.0.1'}</code></td>
                <td style="color: #cbd5e1;">${l.details || '-'}</td>
            </tr>
        `).join('');
    }

    if (logsSearchInput) logsSearchInput.addEventListener('input', renderLogsTable);

    if (btnClearLogs) {
        btnClearLogs.addEventListener('click', async () => {
            if (!confirm('คุณต้องการล้างบันทึกกิจกรรมระบบทั้งหมดหรือไม่?')) return;
            try {
                const res = await fetch('/api/admin/logs', { method: 'DELETE' });
                if (!res.ok) throw new Error('Error clearing logs');
                showToast('ล้างบันทึกกิจกรรมเรียบร้อย');
                loadLogs();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // ==========================================================================
    // 6. SYSTEM SETTINGS
    // ==========================================================================
    const settingsForm = document.getElementById('settings-form');
    const thresholdSlider = document.getElementById('setting-threshold');
    const thresholdDisplay = document.getElementById('threshold-val-display');

    if (thresholdSlider && thresholdDisplay) {
        thresholdSlider.addEventListener('input', () => {
            thresholdDisplay.textContent = `${thresholdSlider.value}%`;
        });
    }

    async function loadSettings() {
        try {
            const res = await fetch('/api/admin/settings');
            if (!res.ok) throw new Error('Cannot fetch settings');
            state.settings = await res.json();

            if (thresholdSlider && state.settings.confidence_threshold) {
                thresholdSlider.value = state.settings.confidence_threshold;
                thresholdDisplay.textContent = `${thresholdSlider.value}%`;
            }
            if (document.getElementById('setting-allow-reg')) {
                document.getElementById('setting-allow-reg').checked = state.settings.allow_registration === 'true';
            }
            if (document.getElementById('setting-allow-guest')) {
                document.getElementById('setting-allow-guest').checked = state.settings.allow_guest_translation === 'true';
            }
            if (document.getElementById('setting-maintenance')) {
                document.getElementById('setting-maintenance').checked = state.settings.maintenance_mode === 'true';
            }
            if (document.getElementById('setting-announcement') && state.settings.announcement) {
                document.getElementById('setting-announcement').value = state.settings.announcement;
            }
        } catch (err) {
            console.error(err);
        }
    }

    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                confidence_threshold: thresholdSlider.value,
                allow_registration: document.getElementById('setting-allow-reg').checked ? 'true' : 'false',
                allow_guest_translation: document.getElementById('setting-allow-guest').checked ? 'true' : 'false',
                maintenance_mode: document.getElementById('setting-maintenance').checked ? 'true' : 'false',
                announcement: document.getElementById('setting-announcement').value.trim()
            };

            try {
                const res = await fetch('/api/admin/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.message || 'Error saving settings');
                showToast('บันทึกการตั้งค่าระบบเรียบร้อยแล้ว');
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // ==========================================================================
    // 7. TRANSLATION CAMERA CONTROLLER (server.py Integration)
    // ==========================================================================
    const camImg = document.getElementById('admin-camera-feed');
    const camStatusPill = document.getElementById('cam-server-status-pill');
    const camStatusDot = document.getElementById('cam-server-status-dot');
    const camStatusText = document.getElementById('cam-server-status-text');
    const camOfflineOverlay = document.getElementById('camera-offline-overlay');
    const btnCamToggle = document.getElementById('btn-cam-toggle');
    const btnCamRefresh = document.getElementById('btn-cam-refresh');
    const btnCamFullscreen = document.getElementById('btn-cam-fullscreen');
    const btnRecheckServer = document.getElementById('btn-recheck-server');
    const btnCopyServerCmd = document.getElementById('btn-copy-server-cmd');
    const hudPrediction = document.getElementById('hud-prediction-text');
    const hudConfidence = document.getElementById('hud-confidence-val');
    const camStreamBox = document.getElementById('camera-stream-box');

    let isCamRunning = true;
    let camPollInterval = null;
    const SERVER_URL = 'http://127.0.0.1:8000';

    async function checkCameraServer() {
        if (!isCamRunning) return;
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            // Ping server.py status endpoint
            const res = await fetch(`${SERVER_URL}/status`, { signal: controller.signal });
            clearTimeout(timeoutId);

            if (res.ok) {
                const data = await res.json();
                setCameraOnline(data);
            } else {
                setCameraOffline();
            }
        } catch (err) {
            setCameraOffline();
        }
    }

    function setCameraOnline(data) {
        if (camStatusDot) {
            camStatusDot.className = 'status-dot dot-green';
        }
        if (camStatusText) {
            camStatusText.textContent = 'server.py Live (8000)';
        }
        if (camOfflineOverlay) {
            camOfflineOverlay.style.display = 'none';
        }

        if (camImg && (!camImg.src || camImg.src.includes('about:blank'))) {
            camImg.src = `${SERVER_URL}/video_feed?t=${Date.now()}`;
        }

        if (data) {
            if (hudPrediction && data.current_prediction) {
                hudPrediction.textContent = data.current_prediction;
            }
            if (hudConfidence && data.confidence_score !== undefined) {
                hudConfidence.textContent = `${data.confidence_score}%`;
            }
        }
    }

    function setCameraOffline() {
        if (camStatusDot) {
            camStatusDot.className = 'status-dot dot-red';
        }
        if (camStatusText) {
            camStatusText.textContent = 'server.py Offline';
        }
        if (camOfflineOverlay) {
            camOfflineOverlay.style.display = 'flex';
        }
        if (hudPrediction) {
            hudPrediction.textContent = 'ไม่ได้เชื่อมต่อ';
        }
        if (hudConfidence) {
            hudConfidence.textContent = '0.0%';
        }
    }

    if (btnCamToggle) {
        btnCamToggle.addEventListener('click', () => {
            isCamRunning = !isCamRunning;
            const textSpan = btnCamToggle.querySelector('.btn-cam-text');
            const icon = btnCamToggle.querySelector('i');

            if (isCamRunning) {
                if (camImg) camImg.src = `${SERVER_URL}/video_feed?t=${Date.now()}`;
                btnCamToggle.classList.remove('active');
                if (textSpan) textSpan.textContent = 'ปิดกล้อง';
                if (icon) icon.className = 'fa-solid fa-video';
                checkCameraServer();
            } else {
                if (camImg) camImg.src = 'about:blank';
                btnCamToggle.classList.add('active');
                if (textSpan) textSpan.textContent = 'เปิดกล้อง';
                if (icon) icon.className = 'fa-solid fa-video-slash';
                if (camStatusDot) camStatusDot.className = 'status-dot dot-yellow';
                if (camStatusText) camStatusText.textContent = 'หยุดชั่วคราว';
            }
        });
    }

    if (btnCamRefresh) {
        btnCamRefresh.addEventListener('click', () => {
            if (camImg && isCamRunning) {
                camImg.src = `${SERVER_URL}/video_feed?t=${Date.now()}`;
                showToast('กำลังเชื่อมต่อสตรีมกล้องใหม่...');
            }
            checkCameraServer();
        });
    }

    if (btnCamFullscreen && camStreamBox) {
        btnCamFullscreen.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                camStreamBox.requestFullscreen().catch(err => {
                    console.error('Error attempting to enable fullscreen:', err);
                });
            } else {
                document.exitFullscreen();
            }
        });
    }

    if (btnRecheckServer) {
        btnRecheckServer.addEventListener('click', () => {
            if (camStatusText) camStatusText.textContent = 'กำลังทดสอบเชื่อมต่อ...';
            if (camImg && isCamRunning) camImg.src = `${SERVER_URL}/video_feed?t=${Date.now()}`;
            checkCameraServer();
        });
    }

    if (btnCopyServerCmd) {
        btnCopyServerCmd.addEventListener('click', () => {
            const cmdText = document.getElementById('cmd-run-server')?.textContent || 'py -3.12 train_AI/server.py';
            navigator.clipboard.writeText(cmdText).then(() => {
                showToast('คัดลอกคำสั่งสำหรับรัน server.py เรียบร้อยแล้ว!');
            }).catch(() => {
                showToast('ไม่สามารถคัดลอกได้ กรุณาคัดลอกด้วยตนเอง', 'error');
            });
        });
    }

    // Monitor camera img load/error
    if (camImg) {
        camImg.addEventListener('error', () => {
            if (isCamRunning) {
                if (camImg.src.includes(':8000')) {
                    // Fallback to proxy
                    camImg.src = `/video_feed?t=${Date.now()}`;
                } else {
                    setCameraOffline();
                }
            }
        });
        camImg.addEventListener('load', () => {
            if (isCamRunning && !camImg.src.includes('about:blank')) {
                setCameraOnline();
            }
        });
    }

    // Polling status
    checkCameraServer();
    camPollInterval = setInterval(checkCameraServer, 3000);

    // Initial Load
    loadOverviewStats();
});
