/**
 * TeamUp by ACE - Platform Expansion Controller (Phases 1 - 8)
 * Handles Opportunities Hub, Jobs & Internships, Resume Builder,
 * Application Tracking, Learn & Assessments, Certificates & Portfolio,
 * Community (Mentors, Alumni, Forums), Role Portals, and Advanced Team Collaboration.
 */

const expansionState = {
    currentOpp: null,
    currentJob: null,
    currentCourse: null,
    activeAssessment: null,
    assessmentTimer: null,
    assessmentSecondsLeft: 900,
    assessmentAnswers: [],
    notifications: [],
    searchResults: null
};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    // Check if initial URL has verify or portfolio
    const path = window.location.pathname;
    if (path.startsWith('/verify/')) {
        const uid = path.replace('/verify/', '');
        window.location.hash = `#verify-${uid}`;
    } else if (path.startsWith('/u/')) {
        const uname = path.replace('/u/', '');
        window.location.hash = `#portfolio-${uname}`;
    }

    // Attach global search listener
    const searchInput = document.getElementById('global-search-input');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const q = e.target.value.trim();
            if (q.length >= 2) {
                debounceTimer = setTimeout(() => executeGlobalSearch(q), 300);
            } else {
                hideGlobalSearchResults();
            }
        });
    }

    // Setup periodic notification polling if logged in
    if (state.token) {
        loadNotifications();
        setInterval(loadNotifications, 60000);
    }
});

// Extend handleHashRouting to support new views
const originalHandleHashRouting = window.handleHashRouting;
window.handleHashRouting = function () {
    const hash = window.location.hash || '#landing';
    hideAllExpansionViews();

    if (hash === '#opportunities') {
        showOpportunitiesView();
    } else if (hash.startsWith('#opp-')) {
        const oppId = parseInt(hash.replace('#opp-', ''));
        showOpportunityDetailView(oppId);
    } else if (hash === '#jobs') {
        showJobsView();
    } else if (hash.startsWith('#job-')) {
        const jobId = parseInt(hash.replace('#job-', ''));
        showJobDetailView(jobId);
    } else if (hash === '#learn') {
        showLearnView();
    } else if (hash.startsWith('#course-')) {
        const cId = parseInt(hash.replace('#course-', ''));
        showCourseDetailView(cId);
    } else if (hash === '#myspace') {
        showMySpaceView();
    } else if (hash === '#community') {
        showCommunityView();
    } else if (hash === '#portal-organizer') {
        showOrganizerPortalView();
    } else if (hash === '#portal-recruiter') {
        showRecruiterPortalView();
    } else if (hash === '#portal-admin') {
        showAdminPortalView();
    } else if (hash.startsWith('#portfolio-')) {
        const identifier = hash.replace('#portfolio-', '');
        showPublicPortfolioView(identifier);
    } else if (hash.startsWith('#verify-')) {
        const uid = hash.replace('#verify-', '');
        showVerifyCertificateView(uid);
    } else {
        // Fall back to original routing
        if (originalHandleHashRouting) originalHandleHashRouting();
    }
    updateNavActiveTabs(hash);
};

function hideAllExpansionViews() {
    const viewIds = [
        'view-opportunities', 'view-opportunity-detail', 'view-jobs',
        'view-learn', 'view-myspace', 'view-community',
        'view-portal-organizer', 'view-portal-recruiter', 'view-portal-admin',
        'view-portfolio', 'view-certificate-verify'
    ];
    viewIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    });
}

function updateNavActiveTabs(hash) {
    document.querySelectorAll('.nav-tab-link').forEach(link => {
        const target = link.getAttribute('href');
        const active = target === hash || (hash.startsWith(target) && target !== '#landing');
        link.classList.toggle('text-indigo-400', active);
        link.classList.toggle('font-bold', active);
        link.classList.toggle('text-slate-300', !active);
    });
}

// ==========================================
// DEMO ROLE QUICK-SWITCHER
// ==========================================
async function switchDemoRole(role) {
    const roleCredentials = {
        student: { email: 'demo@mait.ac.in', password: 'demo1234', title: 'Student (Aarav Sharma - MAIT)' },
        organizer: { email: 'organizer@delhitechexpo.edu', password: 'demo1234', title: 'Organizer (Dr. Rajesh Verma - DTU)' },
        recruiter: { email: 'recruiter@nexuslabs.com', password: 'demo1234', title: 'Recruiter (Pooja Mehra - Nexus Labs)' },
        mentor: { email: 'mentor@aiimsalumni.ac.in', password: 'demo1234', title: 'Mentor (Vikram Malhotra - CloudScale AI)' },
        admin: { email: 'admin@allcollegeevent.com', password: 'admin1234', title: 'Platform Admin (AllCollegeEvent.com)' }
    };

    const creds = roleCredentials[role] || roleCredentials.student;
    showToast(`Switching to ${creds.title}...`, 'info');

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: creds.email, password: creds.password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Role login failed');

        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('teamup_token', state.token);
        updateNavAuthUI();
        updateRoleBadgeUI();
        loadNotifications();

        showToast(`Signed in as ${creds.title}`, 'success');

        // Route to corresponding dashboard
        if (role === 'organizer') window.location.hash = '#portal-organizer';
        else if (role === 'recruiter') window.location.hash = '#portal-recruiter';
        else if (role === 'admin') window.location.hash = '#portal-admin';
        else if (role === 'mentor') window.location.hash = '#community';
        else window.location.hash = '#myspace';
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function updateRoleBadgeUI() {
    const rolePill = document.getElementById('nav-role-badge');
    if (!rolePill) return;

    if (!state.user) {
        rolePill.classList.add('hidden');
        return;
    }

    rolePill.classList.remove('hidden');
    const roleColors = {
        student: 'bg-indigo-950/80 text-indigo-400 border-indigo-800/60',
        organizer: 'bg-amber-950/80 text-amber-400 border-amber-800/60',
        recruiter: 'bg-emerald-950/80 text-emerald-400 border-emerald-800/60',
        mentor: 'bg-purple-950/80 text-purple-400 border-purple-800/60',
        admin: 'bg-rose-950/80 text-rose-400 border-rose-800/60'
    };
    const role = state.user.role || 'student';
    rolePill.className = `inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border ${roleColors[role] || roleColors.student}`;
    rolePill.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-current"></span> ${role.toUpperCase()}`;
}

// Hook into updateNavAuthUI
const origUpdateNavAuthUI = window.updateNavAuthUI;
window.updateNavAuthUI = function () {
    if (origUpdateNavAuthUI) origUpdateNavAuthUI();
    updateRoleBadgeUI();
};

// ==========================================
// UNIFIED GLOBAL SEARCH
// ==========================================
async function executeGlobalSearch(q) {
    const resultsBox = document.getElementById('global-search-results');
    if (!resultsBox) return;

    try {
        const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
        if (!res.ok) return;
        const data = await res.json();
        expansionState.searchResults = data.results;

        renderGlobalSearchResults(data.results, q);
    } catch (err) {
        console.error('Search failed:', err);
    }
}

function renderGlobalSearchResults(results, query) {
    const box = document.getElementById('global-search-results');
    if (!box) return;

    let html = '';
    const hasAny = results.opportunities.length || results.jobs.length || results.courses.length || results.teams.length || results.people.length;

    if (!hasAny) {
        box.innerHTML = `<div class="p-4 text-xs text-slate-400 text-center">No matches found for "${query}"</div>`;
        box.classList.remove('hidden');
        return;
    }

    if (results.opportunities.length) {
        html += `<div class="p-2 text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-slate-900/80">Opportunities</div>`;
        results.opportunities.forEach(o => {
            html += `<a href="${o.url}" onclick="hideGlobalSearchResults()" class="block p-2.5 hover:bg-slate-800/80 text-xs text-white border-b border-slate-800/50">
                <span class="font-semibold">${o.title}</span> <span class="text-[10px] text-slate-400">(${o.type})</span>
            </a>`;
        });
    }

    if (results.jobs.length) {
        html += `<div class="p-2 text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-slate-900/80">Jobs & Internships</div>`;
        results.jobs.forEach(j => {
            html += `<a href="${j.url}" onclick="hideGlobalSearchResults()" class="block p-2.5 hover:bg-slate-800/80 text-xs text-white border-b border-slate-800/50">
                <span class="font-semibold">${j.title}</span> <span class="text-[10px] text-slate-400">• ${j.company}</span>
            </a>`;
        });
    }

    if (results.courses.length) {
        html += `<div class="p-2 text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-slate-900/80">Courses</div>`;
        results.courses.forEach(c => {
            html += `<a href="${c.url}" onclick="hideGlobalSearchResults()" class="block p-2.5 hover:bg-slate-800/80 text-xs text-white border-b border-slate-800/50">
                <span class="font-semibold">${c.title}</span> <span class="text-[10px] text-slate-400">• ${c.level}</span>
            </a>`;
        });
    }

    if (results.people.length) {
        html += `<div class="p-2 text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-slate-900/80">People</div>`;
        results.people.forEach(p => {
            html += `<a href="${p.url}" onclick="hideGlobalSearchResults()" class="block p-2.5 hover:bg-slate-800/80 text-xs text-white border-b border-slate-800/50">
                <span class="font-semibold">${p.name}</span> <span class="text-[10px] text-slate-400">• ${p.college}</span>
            </a>`;
        });
    }

    box.innerHTML = html;
    box.classList.remove('hidden');
}

function hideGlobalSearchResults() {
    const box = document.getElementById('global-search-results');
    if (box) box.classList.add('hidden');
}

// ==========================================
// IN-APP NOTIFICATIONS
// ==========================================
async function loadNotifications() {
    if (!state.token) return;
    try {
        const res = await fetch(`${API_BASE}/notifications`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        expansionState.notifications = data.items;

        const countBadge = document.getElementById('notification-badge');
        if (countBadge) {
            countBadge.innerText = data.unread_count;
            countBadge.classList.toggle('hidden', data.unread_count === 0);
        }
        renderNotificationDropdown(data.items);
    } catch (err) {
        console.error('Failed to load notifications:', err);
    }
}

function renderNotificationDropdown(items) {
    const list = document.getElementById('notification-list');
    if (!list) return;

    if (!items || items.length === 0) {
        list.innerHTML = `<div class="p-6 text-center text-xs text-slate-400">No new notifications.</div>`;
        return;
    }

    list.innerHTML = items.map(n => `
        <div class="p-3.5 border-b border-slate-800/80 hover:bg-slate-800/40 transition cursor-pointer ${!n.is_read ? 'bg-indigo-950/20' : ''}" onclick="handleNotificationClick(${n.id}, '${n.link}')">
            <div class="flex items-start justify-between gap-2">
                <h5 class="text-xs font-bold text-white ${!n.is_read ? 'text-indigo-300' : ''}">${n.title}</h5>
                <span class="text-[10px] text-slate-500 whitespace-nowrap">${n.time}</span>
            </div>
            <p class="text-[11px] text-slate-400 mt-1">${n.message}</p>
        </div>
    `).join('');
}

async function handleNotificationClick(id, link) {
    try {
        await fetch(`${API_BASE}/notifications/${id}/read`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        loadNotifications();
    } catch (err) {}

    if (link) {
        window.location.hash = link;
        toggleNotificationDropdown(false);
    }
}

function toggleNotificationDropdown(forceState) {
    const menu = document.getElementById('notification-dropdown');
    if (!menu) return;
    if (typeof forceState === 'boolean') {
        menu.classList.toggle('hidden', !forceState);
    } else {
        menu.classList.toggle('hidden');
    }
}

async function markAllNotificationsRead() {
    try {
        await fetch(`${API_BASE}/notifications/read-all`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        loadNotifications();
        showToast('All notifications marked as read', 'info');
    } catch (err) {}
}

// ==========================================
// PHASE 1: OPPORTUNITIES HUB
// ==========================================
async function showOpportunitiesView() {
    hideAllViews();
    const el = document.getElementById('view-opportunities');
    if (el) el.classList.remove('hidden');
    await loadOpportunities();
}

async function loadOpportunities(page = 1) {
    const type = document.getElementById('opp-type-filter')?.value || 'All';
    const mode = document.getElementById('opp-mode-filter')?.value || 'All';
    const search = document.getElementById('opp-search')?.value || '';
    const container = document.getElementById('opportunities-grid');
    if (!container) return;

    container.innerHTML = `<div class="col-span-full py-16 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl text-indigo-400"></i><p class="mt-2 text-xs">Loading opportunities...</p></div>`;

    try {
        const queryParams = new URLSearchParams({ page, limit: 12, type, mode, search });
        const res = await fetch(`${API_BASE}/opportunities?${queryParams.toString()}`);
        if (!res.ok) throw new Error('Failed to load opportunities');
        const data = await res.json();

        renderOpportunitiesList(data.items);
        renderPagination('opp-pagination', data.page, data.pages, loadOpportunities);
    } catch (err) {
        container.innerHTML = `<div class="col-span-full py-8 text-center text-rose-400 text-xs">${err.message}</div>`;
    }
}

function renderOpportunitiesList(items) {
    const container = document.getElementById('opportunities-grid');
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `<div class="col-span-full py-16 text-center text-slate-400 glass-card rounded-2xl p-8">
            <i class="fa-solid fa-box-open text-4xl mb-3 text-slate-500"></i>
            <p class="text-sm font-semibold text-white">No opportunities found.</p>
            <p class="text-xs text-slate-400 mt-1">Try resetting filters to explore more events and programs.</p>
        </div>`;
        return;
    }

    container.innerHTML = items.map(o => `
        <div class="glass-card rounded-2xl overflow-hidden flex flex-col group border border-slate-800/80 hover:border-indigo-500/50 transition">
            <div class="relative h-40 overflow-hidden cursor-pointer" onclick="window.location.hash = '#opp-${o.id}'">
                <img src="${o.banner_url}" alt="${o.title}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
                <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent"></div>
                <div class="absolute top-3 left-3 flex flex-wrap gap-1.5">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-600/90 text-white backdrop-blur">${o.type}</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-900/80 text-slate-300 border border-white/10 backdrop-blur">${o.location_mode}</span>
                </div>
                <div class="absolute bottom-3 right-3">
                    <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-400 text-slate-950 shadow">
                        🏆 ${o.prize_pool || o.stipend_ctc || 'Certificate'}
                    </span>
                </div>
            </div>
            <div class="p-5 flex-1 flex flex-col justify-between">
                <div>
                    <h4 class="text-base font-bold text-white group-hover:text-indigo-400 transition cursor-pointer" onclick="window.location.hash = '#opp-${o.id}'">${o.title}</h4>
                    <p class="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                        <i class="fa-solid fa-building-columns text-indigo-400"></i> ${o.organizer_name}
                    </p>
                    <p class="text-xs text-slate-300 mt-3 line-clamp-2">${o.description}</p>
                    <div class="mt-3 flex flex-wrap gap-1">
                        ${(o.skills || []).slice(0, 3).map(s => `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700/60">${s}</span>`).join('')}
                    </div>
                </div>
                <div class="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                    <span class="text-[11px] text-slate-400"><i class="fa-regular fa-clock text-amber-400"></i> ${o.deadline}</span>
                    <div class="flex items-center gap-2">
                        <button onclick="registerForOpportunity(${o.id})" class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow transition">
                            Apply / Register
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

async function showOpportunityDetailView(id) {
    hideAllViews();
    const el = document.getElementById('view-opportunity-detail');
    if (el) el.classList.remove('hidden');

    try {
        const headers = state.token ? { 'Authorization': `Bearer ${state.token}` } : {};
        const res = await fetch(`${API_BASE}/opportunities/${id}`, { headers });
        if (!res.ok) throw new Error('Opportunity not found');
        const o = await res.json();
        expansionState.currentOpp = o;

        document.getElementById('opp-detail-title').innerText = o.title;
        document.getElementById('opp-detail-organizer').innerText = o.organizer_name;
        document.getElementById('opp-detail-type').innerText = o.type;
        document.getElementById('opp-detail-mode').innerText = o.location_mode;
        document.getElementById('opp-detail-venue').innerText = o.location_venue;
        document.getElementById('opp-detail-deadline').innerText = o.deadline;
        document.getElementById('opp-detail-prize').innerText = o.prize_pool || o.stipend_ctc || 'Certification';
        document.getElementById('opp-detail-teamsize').innerText = `${o.team_size_min} - ${o.team_size_max} Members`;
        document.getElementById('opp-detail-desc').innerText = o.description;
        document.getElementById('opp-detail-eligibility').innerText = o.eligibility;
        document.getElementById('opp-detail-banner').src = o.banner_url;

        // Skills chips
        const skillsContainer = document.getElementById('opp-detail-skills');
        if (skillsContainer) {
            skillsContainer.innerHTML = (o.skills || []).map(s => `
                <span class="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 text-indigo-300 border border-indigo-900/60">${s}</span>
            `).join('');
        }

        // Teams formed button
        const findTeammatesBtn = document.getElementById('opp-detail-find-teammates-btn');
        if (findTeammatesBtn) {
            if (o.event_id) {
                findTeammatesBtn.classList.remove('hidden');
                findTeammatesBtn.onclick = () => window.location.hash = `#event-${o.event_id}`;
            } else {
                findTeammatesBtn.classList.add('hidden');
            }
        }

        // Save button state
        const saveBtn = document.getElementById('opp-detail-save-btn');
        if (saveBtn) {
            saveBtn.innerHTML = o.is_saved
                ? `<i class="fa-solid fa-bookmark text-amber-400"></i> Saved`
                : `<i class="fa-regular fa-bookmark"></i> Save`;
        }
    } catch (err) {
        showToast(err.message, 'error');
        window.location.hash = '#opportunities';
    }
}

async function registerForOpportunity(id) {
    if (!state.token) {
        openModal('auth-modal');
        showToast('Please sign in to register', 'info');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/opportunities/${id}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');

        showToast(data.message, 'success');
        if (window.location.hash === `#opp-${id}`) {
            showOpportunityDetailView(id);
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function toggleSaveOpportunity(id) {
    if (!state.token) {
        openModal('auth-modal');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/opportunities/${id}/save`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const data = await res.json();
        showToast(data.message, 'info');
        if (window.location.hash === `#opp-${id}`) {
            showOpportunityDetailView(id);
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// PHASE 2: JOBS & INTERNSHIPS
// ==========================================
async function showJobsView() {
    hideAllViews();
    const el = document.getElementById('view-jobs');
    if (el) el.classList.remove('hidden');
    await loadJobs();
    if (state.token) loadJobRecommendations();
}

async function loadJobs(page = 1) {
    const roleCat = document.getElementById('job-role-filter')?.value || 'All';
    const type = document.getElementById('job-type-filter')?.value || 'All';
    const mode = document.getElementById('job-mode-filter')?.value || 'All';
    const search = document.getElementById('job-search')?.value || '';
    const container = document.getElementById('jobs-grid');
    if (!container) return;

    container.innerHTML = `<div class="col-span-full py-16 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl text-emerald-400"></i><p class="mt-2 text-xs">Loading openings...</p></div>`;

    try {
        const q = new URLSearchParams({ page, limit: 12, role_category: roleCat, job_type: type, work_mode: mode, search });
        const res = await fetch(`${API_BASE}/jobs?${q.toString()}`);
        if (!res.ok) throw new Error('Failed to load jobs');
        const data = await res.json();

        renderJobsList(data.items);
        renderPagination('jobs-pagination', data.page, data.pages, loadJobs);
    } catch (err) {
        container.innerHTML = `<div class="col-span-full py-8 text-center text-rose-400 text-xs">${err.message}</div>`;
    }
}

function renderJobsList(items) {
    const container = document.getElementById('jobs-grid');
    if (!container) return;

    if (!items || items.length === 0) {
        container.innerHTML = `<div class="col-span-full py-16 text-center text-slate-400 glass-card rounded-2xl p-8">
            <i class="fa-solid fa-briefcase text-4xl mb-3 text-slate-500"></i>
            <p class="text-sm font-semibold text-white">No active job openings found.</p>
        </div>`;
        return;
    }

    container.innerHTML = items.map(j => `
        <div class="glass-card rounded-2xl p-5 border border-slate-800/80 hover:border-emerald-500/50 flex flex-col justify-between transition">
            <div>
                <div class="flex items-start justify-between gap-3">
                    <div class="flex items-center gap-3">
                        <img src="${j.company_logo}" alt="${j.company_name}" class="w-10 h-10 rounded-xl object-cover border border-slate-700/80">
                        <div>
                            <h4 class="text-sm font-bold text-white hover:text-emerald-400 transition cursor-pointer" onclick="openJobDetailModal(${j.id})">${j.title}</h4>
                            <p class="text-xs text-slate-400">${j.company_name} • ${j.location}</p>
                        </div>
                    </div>
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800/60">${j.job_type}</span>
                </div>
                <div class="mt-4 flex flex-wrap gap-2 text-xs text-slate-300">
                    <span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800"><i class="fa-solid fa-indian-rupee-sign text-emerald-400"></i> ${j.stipend_salary}</span>
                    <span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800"><i class="fa-solid fa-laptop-house text-indigo-400"></i> ${j.work_mode}</span>
                    <span class="px-2 py-0.5 rounded bg-slate-900 border border-slate-800"><i class="fa-regular fa-clock text-amber-400"></i> ${j.duration}</span>
                </div>
                <div class="mt-3 flex flex-wrap gap-1">
                    ${(j.skills_required || []).map(s => `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">${s}</span>`).join('')}
                </div>
            </div>
            <div class="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span class="text-[10px] text-slate-400">${j.deadline}</span>
                <div class="flex items-center gap-2">
                    <button onclick="openJobDetailModal(${j.id})" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition">
                        View Details
                    </button>
                    <button onclick="openApplyJobModal(${j.id})" class="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition">
                        1-Click Apply
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

async function loadJobRecommendations() {
    const container = document.getElementById('job-recommendations-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/jobs/recommendations`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const recs = await res.json();

        if (!recs || recs.length === 0) {
            container.innerHTML = `<p class="text-xs text-slate-400">Add more skills to your profile to see tailored job recommendations.</p>`;
            return;
        }

        container.innerHTML = recs.map(r => `
            <div class="glass-card p-4 rounded-xl border border-emerald-500/30 flex items-center justify-between gap-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-700/60 flex items-center justify-center font-bold text-emerald-400 text-xs">
                        ${r.match_score}%
                    </div>
                    <div>
                        <h5 class="text-xs font-bold text-white">${r.job.title}</h5>
                        <p class="text-[11px] text-slate-400">${r.job.company_name} • ${r.job.stipend_salary}</p>
                        <p class="text-[10px] text-emerald-400 mt-0.5">✨ ${r.why_recommended}</p>
                    </div>
                </div>
                <button onclick="openApplyJobModal(${r.job.id})" class="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold whitespace-nowrap shadow">
                    Apply
                </button>
            </div>
        `).join('');
    } catch (err) {}
}

async function openJobDetailModal(id) {
    try {
        const res = await fetch(`${API_BASE}/jobs/${id}`);
        if (!res.ok) throw new Error('Job not found');
        const job = await res.json();
        expansionState.currentJob = job;

        document.getElementById('job-modal-title').innerText = job.title;
        document.getElementById('job-modal-company').innerText = job.company_name;
        document.getElementById('job-modal-stipend').innerText = job.stipend_salary;
        document.getElementById('job-modal-mode').innerText = `${job.work_mode} (${job.location})`;
        document.getElementById('job-modal-duration').innerText = job.duration;
        document.getElementById('job-modal-desc').innerText = job.description;

        const skillsBox = document.getElementById('job-modal-skills');
        skillsBox.innerHTML = (job.skills_required || []).map(s => `<span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-emerald-300 border border-emerald-900/60">${s}</span>`).join('');

        const perksBox = document.getElementById('job-modal-perks');
        perksBox.innerHTML = (job.perks || []).map(p => `<li>${p}</li>`).join('');

        openModal('job-detail-modal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function openApplyJobModal(id) {
    if (!state.token) {
        openModal('auth-modal');
        showToast('Please sign in to apply', 'info');
        return;
    }
    expansionState.applyJobId = id;
    openModal('job-apply-modal');
}

async function handleJobApplySubmit(e) {
    e.preventDefault();
    const coverNote = document.getElementById('apply-cover-note').value;
    const expectedStipend = document.getElementById('apply-expected-stipend').value;

    try {
        const res = await fetch(`${API_BASE}/jobs/${expansionState.applyJobId}/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ cover_note: coverNote, expected_stipend: expectedStipend })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Application failed');

        closeModal('job-apply-modal');
        showToast(data.message, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// PHASE 3: MY SPACE & APPLICATION TRACKING
// ==========================================
async function showMySpaceView() {
    if (!state.token) {
        openModal('auth-modal');
        showToast('Please sign in to access My Space', 'info');
        return;
    }
    hideAllViews();
    const el = document.getElementById('view-myspace');
    if (el) el.classList.remove('hidden');
    await loadMyApplications();
    await loadMyResumes();
    await loadMyCertificates();
    await loadMySavedItems();
}

async function loadMyApplications(statusTab = 'all') {
    const container = document.getElementById('myspace-applications-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/applications/my?status_tab=${statusTab}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const data = await res.json();

        // Update counts
        document.getElementById('profile-completeness-bar').style.width = `${data.profile_completeness}%`;
        document.getElementById('profile-completeness-text').innerText = `${data.profile_completeness}%`;

        if (!data.items || data.items.length === 0) {
            container.innerHTML = `<div class="py-12 text-center text-slate-400 glass-card rounded-xl">
                <i class="fa-solid fa-inbox text-3xl mb-2 text-slate-500"></i>
                <p class="text-xs">No applications found in this tab.</p>
            </div>`;
            return;
        }

        container.innerHTML = data.items.map(a => {
            const title = a.opportunity ? a.opportunity.title : (a.job ? a.job.title : 'Application');
            const org = a.opportunity ? a.opportunity.organizer_name : (a.job ? a.job.company_name : '');
            const type = a.opportunity ? a.opportunity.type : (a.job ? a.job.job_type : 'Opportunity');

            const statusColors = {
                'Applied': 'bg-indigo-950 text-indigo-400 border-indigo-800',
                'Registered': 'bg-emerald-950 text-emerald-400 border-emerald-800',
                'Under Review': 'bg-amber-950 text-amber-400 border-amber-800',
                'Shortlisted': 'bg-purple-950 text-purple-400 border-purple-800',
                'Interview': 'bg-cyan-950 text-cyan-400 border-cyan-800',
                'Selected': 'bg-emerald-900 text-emerald-200 border-emerald-600',
                'Rejected': 'bg-rose-950 text-rose-400 border-rose-800',
                'Withdrawn': 'bg-slate-900 text-slate-400 border-slate-700'
            };

            return `
                <div class="glass-card p-5 rounded-2xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${statusColors[a.status] || 'bg-slate-800 text-slate-300'}">${a.status}</span>
                            <span class="text-xs text-slate-400">• ${type}</span>
                        </div>
                        <h4 class="text-base font-bold text-white mt-1">${title}</h4>
                        <p class="text-xs text-slate-400">${org} • Applied on ${a.created_at}</p>
                        ${a.interview_date ? `<p class="text-xs text-cyan-400 font-semibold mt-2"><i class="fa-regular fa-calendar-check mr-1"></i> Interview Scheduled: ${a.interview_date}</p>` : ''}
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="viewApplicationTimeline(${a.id})" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-white font-medium transition">
                            View Timeline
                        </button>
                        ${a.status !== 'Withdrawn' && a.status !== 'Rejected' ? `
                            <button onclick="withdrawApplication(${a.id})" class="px-3 py-1.5 rounded-xl text-xs text-rose-400 hover:bg-rose-950/40 border border-rose-900/40 transition">
                                Withdraw
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {}
}

async function withdrawApplication(id) {
    if (!confirm('Are you sure you want to withdraw this application?')) return;
    try {
        const res = await fetch(`${API_BASE}/applications/${id}/withdraw`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (res.ok) {
            showToast('Application withdrawn', 'info');
            loadMyApplications();
        }
    } catch (err) {}
}

async function loadMyResumes() {
    const container = document.getElementById('myspace-resumes-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/resumes`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const resumes = await res.json();

        container.innerHTML = resumes.map(r => `
            <div class="glass-card p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                    <h5 class="text-xs font-bold text-white flex items-center gap-2">
                        ${r.title} ${r.is_default ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">Default</span>' : ''}
                    </h5>
                    <p class="text-[11px] text-slate-400 mt-0.5">Template: ${r.template_name} • Updated ${r.updated_at}</p>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="previewResume(${r.id})" class="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition" title="Preview Resume">
                        <i class="fa-solid fa-eye text-xs"></i>
                    </button>
                    ${!r.is_default ? `
                        <button onclick="setDefaultResume(${r.id})" class="px-2 py-1 rounded text-[11px] bg-slate-800 text-slate-300 hover:text-white transition">
                            Make Default
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (err) {}
}

async function loadMyCertificates() {
    const container = document.getElementById('myspace-certificates-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/certificates/my`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const certs = await res.json();

        container.innerHTML = certs.map(c => `
            <div class="glass-card p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500/20 to-indigo-500/20 flex items-center justify-center text-amber-400">
                        <i class="fa-solid fa-certificate"></i>
                    </div>
                    <div>
                        <h5 class="text-xs font-bold text-white">${c.title}</h5>
                        <p class="text-[11px] text-slate-400">ID: ${c.unique_id} • Issued by ${c.issuer}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <a href="#verify-${c.unique_id}" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-white font-medium transition flex items-center gap-1.5">
                        <i class="fa-solid fa-qrcode text-amber-400"></i> Verify
                    </a>
                </div>
            </div>
        `).join('');
    } catch (err) {}
}

async function loadMySavedItems() {
    const container = document.getElementById('myspace-saved-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/applications/saved`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const items = await res.json();

        if (!items || items.length === 0) {
            container.innerHTML = `<p class="text-xs text-slate-400">No saved items yet.</p>`;
            return;
        }

        container.innerHTML = items.map(s => `
            <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                    <h6 class="text-xs font-bold text-white">${s.data.title}</h6>
                    <p class="text-[11px] text-slate-400">${s.data.organizer || s.data.company} • ${s.item_type.toUpperCase()}</p>
                </div>
                <button onclick="toggleSaveItem('${s.item_type}', ${s.item_id})" class="text-slate-500 hover:text-rose-400 text-xs">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `).join('');
    } catch (err) {}
}

async function toggleSaveItem(type, id) {
    try {
        await fetch(`${API_BASE}/applications/saved/toggle?item_type=${type}&item_id=${id}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        loadMySavedItems();
    } catch (err) {}
}

// ==========================================
// PHASE 4: LEARN: COURSES & ASSESSMENTS
// ==========================================
async function showLearnView() {
    hideAllViews();
    const el = document.getElementById('view-learn');
    if (el) el.classList.remove('hidden');
    await loadCourses();
    await loadLearningPaths();
    await loadAssessments();
}

async function loadCourses(page = 1) {
    const skill = document.getElementById('course-skill-filter')?.value || 'All';
    const level = document.getElementById('course-level-filter')?.value || 'All';
    const search = document.getElementById('course-search')?.value || '';
    const container = document.getElementById('courses-grid');
    if (!container) return;

    container.innerHTML = `<div class="col-span-full py-16 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl text-purple-400"></i></div>`;

    try {
        const q = new URLSearchParams({ page, limit: 12, skill, level, search });
        const res = await fetch(`${API_BASE}/learn/courses?${q.toString()}`);
        if (!res.ok) return;
        const data = await res.json();

        container.innerHTML = data.items.map(c => `
            <div class="glass-card rounded-2xl overflow-hidden flex flex-col justify-between border border-slate-800/80 hover:border-purple-500/50 transition">
                <div class="relative h-36 overflow-hidden">
                    <img src="${c.thumbnail_url}" alt="${c.title}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent"></div>
                    <span class="absolute top-3 left-3 px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950/90 text-purple-300 border border-purple-800/60 backdrop-blur">${c.level}</span>
                    <span class="absolute bottom-3 right-3 px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900/80 text-white backdrop-blur"><i class="fa-solid fa-star text-amber-400 mr-1"></i>${c.rating}</span>
                </div>
                <div class="p-4 flex-1 flex flex-col justify-between">
                    <div>
                        <h4 class="text-xs font-bold text-white hover:text-purple-400 transition cursor-pointer" onclick="window.location.hash = '#course-${c.id}'">${c.title}</h4>
                        <p class="text-[11px] text-slate-400 mt-1 line-clamp-2">${c.description}</p>
                    </div>
                    <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                        <span class="text-[11px] text-slate-400"><i class="fa-regular fa-clock"></i> ${c.duration}</span>
                        <button onclick="window.location.hash = '#course-${c.id}'" class="px-3 py-1 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow">
                            Start Course
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        renderPagination('courses-pagination', data.page, data.pages, loadCourses);
    } catch (err) {}
}

async function showCourseDetailView(id) {
    hideAllViews();
    const el = document.getElementById('view-learn');
    if (el) el.classList.remove('hidden');

    try {
        const headers = state.token ? { 'Authorization': `Bearer ${state.token}` } : {};
        const res = await fetch(`${API_BASE}/learn/courses/${id}`, { headers });
        if (!res.ok) throw new Error('Course not found');
        const c = await res.json();
        expansionState.currentCourse = c;

        document.getElementById('course-detail-modal-title').innerText = c.title;
        document.getElementById('course-detail-modal-desc').innerText = c.description;
        document.getElementById('course-detail-modal-instructor').innerText = `${c.instructor_name} (${c.instructor_title})`;
        document.getElementById('course-detail-progress-bar').style.width = `${c.progress}%`;
        document.getElementById('course-detail-progress-text').innerText = `${c.progress}% Complete`;

        const modulesBox = document.getElementById('course-modules-list');
        modulesBox.innerHTML = c.modules.map(m => `
            <div class="p-3 rounded-xl bg-slate-900 border border-slate-800">
                <h5 class="text-xs font-bold text-white mb-2">${m.title}</h5>
                <div class="space-y-1.5">
                    ${m.lessons.map(l => `
                        <div class="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 hover:bg-slate-800 text-xs transition">
                            <span class="text-slate-300"><i class="fa-regular fa-circle-play mr-2 text-purple-400"></i> ${l.title}</span>
                            <button onclick="completeLesson(${l.id})" class="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-600 hover:bg-indigo-500 text-white">
                                Mark Done
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');

        openModal('course-detail-modal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function completeLesson(lessonId) {
    if (!state.token) {
        openModal('auth-modal');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/learn/lessons/${lessonId}/complete`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed');

        showToast(data.message, 'success');
        document.getElementById('course-detail-progress-bar').style.width = `${data.progress}%`;
        document.getElementById('course-detail-progress-text').innerText = `${data.progress}% Complete`;

        if (data.issued_certificate_id) {
            showToast(`🎉 Course completed! Certificate ${data.issued_certificate_id} added to your profile!`, 'success');
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadLearningPaths() {
    const container = document.getElementById('learning-paths-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/learn/paths`);
        if (!res.ok) return;
        const paths = await res.json();

        container.innerHTML = paths.map(p => `
            <div class="glass-card p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
                <div>
                    <div class="w-10 h-10 rounded-xl bg-purple-950/80 border border-purple-800/60 flex items-center justify-center text-purple-400 mb-3">
                        <i class="fa-solid ${p.badge_icon}"></i>
                    </div>
                    <h4 class="text-sm font-bold text-white">${p.title}</h4>
                    <p class="text-xs text-slate-400 mt-1">${p.description}</p>
                    <div class="mt-3 text-[11px] text-slate-300">
                        <span class="font-semibold text-purple-400">${p.courses_count} Core Courses</span> + Capstone Project
                    </div>
                </div>
                <div class="mt-4 pt-3 border-t border-slate-800">
                    <p class="text-[10px] text-slate-500 font-mono">Target: ${p.role_target}</p>
                </div>
            </div>
        `).join('');
    } catch (err) {}
}

async function loadAssessments() {
    const container = document.getElementById('assessments-grid');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/learn/assessments`);
        if (!res.ok) return;
        const items = await res.json();

        container.innerHTML = items.map(a => `
            <div class="glass-card p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                    <h5 class="text-xs font-bold text-white">${a.title}</h5>
                    <p class="text-[11px] text-slate-400">${a.duration_minutes} Mins • Target Skill: ${a.skill_name} (Level ${a.level})</p>
                </div>
                <button onclick="startAssessmentModal(${a.id})" class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow">
                    Take Test
                </button>
            </div>
        `).join('');
    } catch (err) {}
}

async function startAssessmentModal(id) {
    if (!state.token) {
        openModal('auth-modal');
        showToast('Please sign in to take skill assessments', 'info');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/learn/assessments/${id}`);
        if (!res.ok) throw new Error('Failed to load assessment');
        const a = await res.json();
        expansionState.activeAssessment = a;
        expansionState.assessmentAnswers = new Array(a.questions.length).fill(0);

        document.getElementById('assessment-modal-title').innerText = a.title;
        document.getElementById('assessment-modal-desc').innerText = a.description;

        const qBox = document.getElementById('assessment-questions-container');
        qBox.innerHTML = a.questions.map((q, idx) => `
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <p class="text-xs font-bold text-white">${idx + 1}. ${q.question}</p>
                <div class="space-y-1">
                    ${q.options.map((opt, oIdx) => `
                        <label class="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800 cursor-pointer text-xs text-slate-300">
                            <input type="radio" name="q_${idx}" value="${oIdx}" ${oIdx === 0 ? 'checked' : ''} onchange="expansionState.assessmentAnswers[${idx}] = ${oIdx}">
                            <span>${opt}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `).join('');

        openModal('assessment-runner-modal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function submitAssessmentExam() {
    if (!expansionState.activeAssessment) return;
    try {
        const res = await fetch(`${API_BASE}/learn/assessments/${expansionState.activeAssessment.id}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ answers: expansionState.assessmentAnswers })
        });
        const data = await res.json();
        closeModal('assessment-runner-modal');

        if (data.passed) {
            showToast(`🏆 Benchmark Passed! ${data.message}`, 'success');
            // Refresh user profile in state
            await fetchCurrentUser();
            updateNavAuthUI();
        } else {
            showToast(data.message, 'warning');
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// PHASE 5: PUBLIC VERIFY & DIGITAL PORTFOLIO
// ==========================================
async function showVerifyCertificateView(uniqueId) {
    hideAllViews();
    const el = document.getElementById('view-certificate-verify');
    if (el) el.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/certificates/verify/${uniqueId}`);
        const box = document.getElementById('cert-verify-card');
        if (!res.ok) {
            box.innerHTML = `<div class="p-8 text-center text-rose-400 glass-card rounded-2xl">
                <i class="fa-solid fa-triangle-exclamation text-4xl mb-3"></i>
                <h3 class="text-lg font-bold">Invalid Credential</h3>
                <p class="text-xs text-slate-400 mt-1">No verified credential found matching ID: ${uniqueId}</p>
            </div>`;
            return;
        }
        const cert = await res.json();

        box.innerHTML = `
            <div class="glass-card p-8 rounded-3xl border-2 border-amber-500/40 relative overflow-hidden max-w-xl mx-auto shadow-2xl">
                <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-emerald-400 animate-ping"></span>
                        <span class="text-xs font-bold text-emerald-400 uppercase tracking-widest">Officially Verified Credential</span>
                    </div>
                    <span class="text-xs text-slate-400 font-mono">${cert.unique_id}</span>
                </div>
                <div class="text-center py-8 space-y-3">
                    <p class="text-xs uppercase tracking-widest text-slate-400">This certifies that</p>
                    <h2 class="text-2xl sm:text-3xl font-black text-white">${cert.recipient_name}</h2>
                    <p class="text-xs text-slate-400">${cert.holder_college}</p>
                    <div class="py-3">
                        <p class="text-sm font-semibold text-indigo-400">has successfully accomplished</p>
                        <h4 class="text-xl font-extrabold text-amber-300 mt-1">${cert.title}</h4>
                    </div>
                </div>
                <div class="border-t border-slate-800 pt-4 flex items-center justify-between text-xs text-slate-400">
                    <div>
                        <p class="font-bold text-white">${cert.issuer}</p>
                        <p class="text-[10px]">Issued: ${cert.issue_date}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-emerald-400 font-bold"><i class="fa-solid fa-circle-check mr-1"></i> Valid & Authentic</p>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {}
}

async function showPublicPortfolioView(identifier) {
    hideAllViews();
    const el = document.getElementById('view-portfolio');
    if (el) el.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/portfolio/u/${identifier}`);
        if (!res.ok) throw new Error('Portfolio not found');
        const p = await res.json();

        document.getElementById('portfolio-avatar').src = p.avatar_url;
        document.getElementById('portfolio-name').innerText = p.name;
        document.getElementById('portfolio-headline').innerText = p.headline;
        document.getElementById('portfolio-college').innerText = `${p.college} • ${p.year}`;
        document.getElementById('portfolio-bio').innerText = p.bio || 'Verified student on ACE TeamUp.';
        document.getElementById('portfolio-reliability').innerText = `${p.reliability_score}/100`;

        // Skills with verified badges
        const skillsBox = document.getElementById('portfolio-skills-list');
        skillsBox.innerHTML = p.skills.map(s => `
            <div class="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                    <span class="text-xs font-bold text-white">${s.name}</span>
                    <span class="text-[10px] text-slate-400 ml-1.5 font-mono">Lvl ${s.level}</span>
                </div>
                ${s.is_verified ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800"><i class="fa-solid fa-check"></i> Verified</span>` : ''}
            </div>
        `).join('');

        // Certificates
        const certsBox = document.getElementById('portfolio-certs-list');
        certsBox.innerHTML = p.certificates.map(c => `
            <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                    <h6 class="text-xs font-bold text-white">${c.title}</h6>
                    <p class="text-[10px] text-slate-400">${c.issuer} • ${c.issue_date}</p>
                </div>
                <a href="${c.verify_url}" class="text-xs text-amber-400 hover:underline">Verify</a>
            </div>
        `).join('');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// PHASE 6: COMMUNITY (MENTORS & FORUMS)
// ==========================================
async function showCommunityView() {
    hideAllViews();
    const el = document.getElementById('view-community');
    if (el) el.classList.remove('hidden');
    await loadMentors();
    await loadAlumni();
    await loadForumThreads();
}

async function loadMentors() {
    const container = document.getElementById('community-mentors-grid');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/community/mentors`);
        if (!res.ok) return;
        const mentors = await res.json();

        container.innerHTML = mentors.map(m => `
            <div class="glass-card p-5 rounded-2xl border border-slate-800 flex flex-col justify-between">
                <div>
                    <div class="flex items-center gap-3">
                        <img src="${m.avatar_url}" alt="${m.name}" class="w-12 h-12 rounded-xl object-cover border border-slate-700">
                        <div>
                            <h4 class="text-sm font-bold text-white">${m.name}</h4>
                            <p class="text-xs text-indigo-400">${m.job_title} @ ${m.company}</p>
                            <p class="text-[10px] text-slate-400 mt-0.5"><i class="fa-solid fa-star text-amber-400"></i> ${m.rating} (${m.sessions_count} sessions)</p>
                        </div>
                    </div>
                    <p class="text-xs text-slate-300 mt-3 line-clamp-2">${m.bio}</p>
                    <div class="mt-3 flex flex-wrap gap-1">
                        ${(m.expertise_skills || []).map(s => `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">${s}</span>`).join('')}
                    </div>
                </div>
                <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span class="text-[10px] text-slate-400">Available: ${m.available_slots[0] || 'Flexible'}</span>
                    <button onclick="openBookMentorModal(${m.user_id}, '${m.name}')" class="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow">
                        Book 1:1
                    </button>
                </div>
            </div>
        `).join('');
    } catch (err) {}
}

async function loadAlumni() {
    const container = document.getElementById('community-alumni-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/community/alumni`);
        if (!res.ok) return;
        const alumni = await res.json();

        container.innerHTML = alumni.slice(0, 10).map(a => `
            <div class="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                <div>
                    <h5 class="text-xs font-bold text-white">${a.name}</h5>
                    <p class="text-[11px] text-slate-400">${a.current_role} @ ${a.company} • Batch of ${a.graduation_year}</p>
                    <p class="text-[10px] text-slate-500">${a.college}</p>
                </div>
                <button onclick="openRequestReferralModal(${a.user_id}, '${a.name}', '${a.company}')" class="px-3 py-1 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow">
                    Ask Referral
                </button>
            </div>
        `).join('');
    } catch (err) {}
}

async function loadForumThreads() {
    const container = document.getElementById('community-forum-list');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/community/forum/threads`);
        if (!res.ok) return;
        const threads = await res.json();

        container.innerHTML = threads.map(t => `
            <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition">
                <h5 class="text-xs font-bold text-white">${t.title}</h5>
                <p class="text-xs text-slate-300 mt-1">${t.content}</p>
                <div class="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                    <span>by ${t.author_name} (${t.author_college}) • ${t.created_at}</span>
                    <span class="flex items-center gap-3">
                        <span><i class="fa-regular fa-comment text-indigo-400 mr-1"></i> ${t.replies_count}</span>
                        <span><i class="fa-regular fa-thumbs-up text-amber-400 mr-1"></i> ${t.upvotes_count}</span>
                    </span>
                </div>
            </div>
        `).join('');
    } catch (err) {}
}

// ==========================================
// PHASE 7: ROLE PORTALS
// ==========================================
async function showOrganizerPortalView() {
    hideAllViews();
    const el = document.getElementById('view-portal-organizer');
    if (el) el.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/portals/organizer/dashboard`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Organizer access required');
        const data = await res.json();

        document.getElementById('org-metric-opps').innerText = data.total_opportunities;
        document.getElementById('org-metric-regs').innerText = data.total_registrations;
        document.getElementById('org-metric-hackathons').innerText = data.active_hackathons;

        const oppsBox = document.getElementById('org-opportunities-table');
        oppsBox.innerHTML = data.opportunities.map(o => `
            <tr class="border-b border-slate-800/80 text-xs text-slate-300">
                <td class="p-3 font-bold text-white">${o.title}</td>
                <td class="p-3">${o.type}</td>
                <td class="p-3 font-semibold text-emerald-400">${o.registrations_count}</td>
                <td class="p-3 font-semibold text-indigo-400">${o.teams_formed}</td>
                <td class="p-3">${o.status}</td>
                <td class="p-3"><button onclick="viewOppApplicants(${o.id})" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white text-[11px]">Review</button></td>
            </tr>
        `).join('');
    } catch (err) {
        showToast(err.message, 'error');
        window.location.hash = '#landing';
    }
}

async function showRecruiterPortalView() {
    hideAllViews();
    const el = document.getElementById('view-portal-recruiter');
    if (el) el.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/portals/recruiter/dashboard`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Recruiter access required');
        const data = await res.json();

        document.getElementById('rec-metric-openings').innerText = data.active_openings;
        document.getElementById('rec-metric-applicants').innerText = data.total_applicants;
        document.getElementById('rec-company-title').innerText = data.company_name;

        await executeRecruiterTalentSearch();
    } catch (err) {
        showToast(err.message, 'error');
        window.location.hash = '#landing';
    }
}

async function executeRecruiterTalentSearch(page = 1) {
    const skill = document.getElementById('talent-skill-filter')?.value || 'All';
    const college = document.getElementById('talent-college-filter')?.value || 'All';
    const verifiedOnly = document.getElementById('talent-verified-check')?.checked || false;
    const container = document.getElementById('talent-search-grid');
    if (!container) return;

    try {
        const q = new URLSearchParams({ page, limit: 12, skill, college, verified_only: verifiedOnly });
        const res = await fetch(`${API_BASE}/portals/recruiter/talent-search?${q.toString()}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('talent-count-badge').innerText = `${data.total} Candidates`;

        container.innerHTML = data.students.map(s => `
            <div class="glass-card p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
                <div>
                    <div class="flex items-center gap-3">
                        <img src="${s.avatar_url}" alt="${s.name}" class="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700">
                        <div>
                            <h5 class="text-xs font-bold text-white">${s.name}</h5>
                            <p class="text-[11px] text-slate-400">${s.college}</p>
                            <p class="text-[10px] text-emerald-400 font-semibold">Reliability: ${s.reliability_score}/100</p>
                        </div>
                    </div>
                    <div class="mt-3 flex flex-wrap gap-1">
                        ${s.skills.slice(0, 3).map(sk => `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">${sk}</span>`).join('')}
                    </div>
                </div>
                <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span class="text-[10px] text-slate-400">${s.certificates_count} Certs</span>
                    <a href="#portfolio-${s.student_id}" class="px-3 py-1 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow">
                        View Profile
                    </a>
                </div>
            </div>
        `).join('');

        renderPagination('talent-pagination', data.page, data.pages, executeRecruiterTalentSearch);
    } catch (err) {}
}

async function showAdminPortalView() {
    hideAllViews();
    const el = document.getElementById('view-portal-admin');
    if (el) el.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/portals/admin/dashboard`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Admin access required');
        const data = await res.json();

        document.getElementById('admin-metric-users').innerText = data.metrics.total_users;
        document.getElementById('admin-metric-opps').innerText = data.metrics.opportunities;
        document.getElementById('admin-metric-jobs').innerText = data.metrics.jobs;
        document.getElementById('admin-metric-teams').innerText = data.metrics.teams;
    } catch (err) {
        showToast(err.message, 'error');
        window.location.hash = '#landing';
    }
}

// ==========================================
// PHASE 8: ADVANCED TEAM COLLABORATION
// ==========================================
async function openWhatIfSimulator(teamId) {
    if (!state.token) {
        openModal('auth-modal');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/teams/${teamId}/what-if`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Failed to run simulator');
        const sim = await res.json();

        document.getElementById('whatif-team-name').innerText = sim.team_name;
        document.getElementById('whatif-candidate-name').innerText = sim.candidate_name;
        document.getElementById('whatif-before-pct').innerText = `${sim.before.coverage_percent}%`;
        document.getElementById('whatif-after-pct').innerText = `${sim.after.coverage_percent}%`;
        document.getElementById('whatif-boost-pill').innerText = `+${sim.coverage_boost}% Capability Boost`;
        document.getElementById('whatif-verdict').innerText = sim.verdict;

        const filledBox = document.getElementById('whatif-filled-skills');
        filledBox.innerHTML = (sim.after.skills_filled_by_you || []).map(s => `
            <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-700/80">
                <i class="fa-solid fa-bolt mr-1"></i> ${s}
            </span>
        `).join('') || '<span class="text-xs text-slate-400">Team already covers required baseline</span>';

        openModal('what-if-modal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadTeamTasks(teamId) {
    const container = document.getElementById('team-kanban-board');
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/teams/${teamId}/tasks`);
        if (!res.ok) return;
        const tasks = await res.json();

        const todoBox = document.getElementById('kanban-todo');
        const inProgBox = document.getElementById('kanban-in-progress');
        const doneBox = document.getElementById('kanban-done');

        if (todoBox) todoBox.innerHTML = '';
        if (inProgBox) inProgBox.innerHTML = '';
        if (doneBox) doneBox.innerHTML = '';

        tasks.forEach(t => {
            const card = `
                <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5 cursor-pointer">
                    <p class="text-xs font-bold text-white">${t.title}</p>
                    <div class="flex items-center justify-between text-[10px] text-slate-400">
                        <span>${t.assigned_to}</span>
                        <span class="capitalize text-amber-400 font-semibold">${t.priority}</span>
                    </div>
                </div>
            `;
            if (t.status === 'todo' && todoBox) todoBox.innerHTML += card;
            else if (t.status === 'in_progress' && inProgBox) inProgBox.innerHTML += card;
            else if (t.status === 'done' && doneBox) doneBox.innerHTML += card;
        });
    } catch (err) {}
}


// ==========================================
// EXPANSION MODALS & ACTION HANDLERS (PHASES 1-8)
// ==========================================

// --- 1. MENTOR BOOKING ---
function openBookMentorModal(mentorUserId, mentorName) {
    if (!state.token) { openModal('auth-modal'); return; }
    const nameInput = document.getElementById('book-mentor-name');
    const idInput   = document.getElementById('book-mentor-id');
    if (nameInput) nameInput.value = mentorName;
    if (idInput)   idInput.value   = mentorUserId;
    openModal('book-mentor-modal');
}

async function handleBookMentorSubmit(e) {
    e.preventDefault();
    const mentorId = document.getElementById('book-mentor-id') ?
        document.getElementById('book-mentor-id').value : null;
    const slot     = document.getElementById('book-mentor-slot').value;
    const topic    = document.getElementById('book-mentor-topic').value.trim();
    if (!topic) { showToast('Please enter a session topic.', 'warning'); return; }
    try {
        const res = await fetch(`${API_BASE}/community/mentors/book`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({ mentor_id: parseInt(mentorId), scheduled_at: slot, topic: topic })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Booking failed');
        closeModal('book-mentor-modal');
        showToast(`Session booked with mentor for "${slot}"! 🎓`, 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 2. REFERRAL REQUEST ---
function openRequestReferralModal(alumniId, alumniName, company) {
    if (!state.token) { openModal('auth-modal'); return; }
    const nameEl = document.getElementById('ref-alumni-name');
    const compEl = document.getElementById('ref-company-name');
    const idEl   = document.getElementById('ref-alumni-id-hidden');
    const jobEl  = document.getElementById('ref-job-url');
    const resEl  = document.getElementById('ref-resume-link');
    const msgEl  = document.getElementById('ref-message');

    if (nameEl) nameEl.textContent = alumniName;
    if (compEl) compEl.textContent = company;
    if (idEl)   idEl.value         = alumniId;
    if (jobEl)  jobEl.value        = '';
    if (resEl)  resEl.value        = '';
    if (msgEl)  msgEl.value        = '';
    openModal('referral-request-modal');
}

async function handleReferralRequestSubmit(e) {
    e.preventDefault();
    const alumniId   = document.getElementById('ref-alumni-id-hidden').value;
    const jobUrl     = document.getElementById('ref-job-url').value.trim();
    const resumeLink = document.getElementById('ref-resume-link').value.trim();
    const message    = document.getElementById('ref-message').value.trim();
    if (!jobUrl || !resumeLink || !message) {
        showToast('Please complete all referral request fields.', 'warning');
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/community/alumni/referral-request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({
                alumni_id: parseInt(alumniId),
                job_url: jobUrl,
                resume_link: resumeLink,
                note: message
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Referral request failed');
        closeModal('referral-request-modal');
        showToast('Referral request sent! The alumni will review it shortly. 🤝', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 3. FORUM THREAD CREATE ---
function openForumCreateModal() {
    if (!state.token) { openModal('auth-modal'); return; }
    const titleEl = document.getElementById('forum-create-title');
    const bodyEl  = document.getElementById('forum-create-body');
    if (titleEl) titleEl.value = '';
    if (bodyEl)  bodyEl.value  = '';
    openModal('forum-create-modal');
}

async function handleForumCreateSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('forum-create-title').value.trim();
    const body  = document.getElementById('forum-create-body').value.trim();
    const tag   = document.getElementById('forum-create-tag').value;
    if (!title || !body) { showToast('Please fill in title and discussion content.', 'warning'); return; }
    try {
        const res = await fetch(`${API_BASE}/community/forum/threads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({ title, content: body, skill_name: tag })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to post discussion');
        closeModal('forum-create-modal');
        showToast('Discussion posted! 💬', 'success');
        showCommunityView();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 4. ORGANIZER: CREATE OPPORTUNITY ---
async function handleCreateOpportunitySubmit(e) {
    e.preventDefault();
    if (!state.token) { openModal('auth-modal'); return; }
    const title     = document.getElementById('create-opp-title').value.trim();
    const oppType   = document.getElementById('create-opp-type').value;
    const mode      = document.getElementById('create-opp-mode').value;
    const deadline  = document.getElementById('create-opp-deadline').value.trim();
    const prize     = document.getElementById('create-opp-prize').value.trim();
    const skillsRaw = document.getElementById('create-opp-skills').value.trim();
    const minTeam   = parseInt(document.getElementById('create-opp-team-min').value || '1');
    const maxTeam   = parseInt(document.getElementById('create-opp-team-max').value || '4');
    const desc      = document.getElementById('create-opp-desc').value.trim();

    const skills = skillsRaw.split(',').map(s => s.trim()).filter(Boolean);

    try {
        const res = await fetch(`${API_BASE}/portals/organizer/opportunities`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({
                title: title,
                type: oppType,
                description: desc,
                skills: skills,
                location_mode: mode,
                deadline: deadline,
                prize_pool: prize,
                team_size_min: minTeam,
                team_size_max: maxTeam
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to publish opportunity');
        closeModal('create-opp-modal');
        showToast(`Opportunity "${title}" published live! 🚀`, 'success');
        showOrganizerPortalView();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 5. JOB ALERT CREATION ---
async function handleCreateJobAlertSubmit(e) {
    e.preventDefault();
    if (!state.token) { openModal('auth-modal'); return; }
    const keyword  = document.getElementById('alert-keyword').value.trim();
    const role     = document.getElementById('alert-role').value;
    const location = document.getElementById('alert-location').value;
    const stipend  = document.getElementById('alert-min-stipend').value;

    try {
        const res = await fetch(`${API_BASE}/jobs/alerts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({
                keyword: keyword,
                role: role,
                location: location,
                min_stipend: stipend
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to save job alert');
        closeModal('job-alert-modal');
        showToast('Job alert activated! You will receive in-app notifications for matches. 🔔', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 6. RESUME BUILDER: CREATE RESUME ---
async function handleCreateResumeSubmit(e) {
    e.preventDefault();
    if (!state.token) { openModal('auth-modal'); return; }
    const title    = document.getElementById('resume-title').value.trim() || 'My Resume';
    const template = document.getElementById('resume-template').value;
    const summary  = document.getElementById('resume-summary').value.trim();
    const skillsRaw= document.getElementById('resume-skills').value.trim();
    const skills   = skillsRaw.split(',').map(s => s.trim()).filter(Boolean);

    const expRole  = document.getElementById('resume-exp-role').value.trim();
    const expOrg   = document.getElementById('resume-exp-org').value.trim();
    const expDur   = document.getElementById('resume-exp-duration').value.trim();
    const expDesc  = document.getElementById('resume-exp-desc').value.trim();

    const eduDeg   = document.getElementById('resume-edu-degree').value.trim();
    const eduCol   = document.getElementById('resume-edu-college').value.trim();
    const eduYear  = document.getElementById('resume-edu-year').value.trim();

    const experience = expRole ? [{ role: expRole, company: expOrg, duration: expDur, description: expDesc }] : [];
    const education  = eduDeg  ? [{ degree: eduDeg, college: eduCol, year: eduYear }] : [];

    try {
        const res = await fetch(`${API_BASE}/resumes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({
                title: title,
                template_name: template,
                data: {
                    summary: summary,
                    skills: skills,
                    experience: experience,
                    education: education
                }
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to create resume');
        closeModal('resume-create-modal');
        showToast(`Resume "${title}" created successfully! 📄`, 'success');
        showMySpaceView();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 7. RESUME PREVIEW & DEFAULT ---
async function previewResume(resumeId) {
    try {
        const res = await fetch(`${API_BASE}/resumes/${resumeId}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Could not load resume');
        const r = await res.json();

        const data = r.data || {};
        const skills = data.skills || [];
        const exp = data.experience || [];
        const edu = data.education || [];

        const existing = document.getElementById('resume-preview-modal-dyn');
        if (existing) existing.remove();

        const div = document.createElement('div');
        div.id = 'resume-preview-modal-dyn';
        div.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm';
        div.innerHTML = `
            <div class="glass-card w-full max-w-lg rounded-3xl border border-slate-800 p-6 space-y-4 max-h-[88vh] overflow-y-auto">
                <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div>
                        <h3 class="text-base font-bold text-white">${r.title || 'Resume Preview'}</h3>
                        <p class="text-xs text-slate-400 capitalize">${r.template_name || 'Modern'} Template</p>
                    </div>
                    <button onclick="document.getElementById('resume-preview-modal-dyn').remove()" class="text-slate-400 hover:text-white">
                        <i class="fa-solid fa-xmark text-lg"></i>
                    </button>
                </div>
                <div class="space-y-3 text-xs">
                    <div>
                        <p class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-1">Summary</p>
                        <p class="text-white leading-relaxed">${data.summary || 'No summary provided.'}</p>
                    </div>
                    <div>
                        <p class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-1">Skills</p>
                        <div class="flex flex-wrap gap-1">
                            ${skills.map(s => `<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">${s}</span>`).join('') || '<span class="text-slate-500">None</span>'}
                        </div>
                    </div>
                    <div>
                        <p class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-1">Experience</p>
                        <div class="space-y-2">
                            ${exp.map(x => `
                                <div class="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
                                    <p class="font-bold text-white">${x.role || 'Role'} @ ${x.company || ''}</p>
                                    <p class="text-[10px] text-slate-400">${x.duration || ''}</p>
                                    <p class="text-slate-300 mt-1">${x.description || ''}</p>
                                </div>
                            `).join('') || '<span class="text-slate-500">No experience added.</span>'}
                        </div>
                    </div>
                    <div>
                        <p class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider mb-1">Education</p>
                        <div class="space-y-1.5">
                            ${edu.map(d => `
                                <div class="p-2 rounded-xl bg-slate-900 border border-slate-800 flex justify-between">
                                    <span class="font-semibold text-white">${d.degree || ''} — ${d.college || ''}</span>
                                    <span class="text-slate-400 text-[10px]">${d.year || ''}</span>
                                </div>
                            `).join('') || '<span class="text-slate-500">No education added.</span>'}
                        </div>
                    </div>
                </div>
                <div class="pt-3 border-t border-slate-800 flex justify-end">
                    <button onclick="document.getElementById('resume-preview-modal-dyn').remove()" class="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(div);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function setDefaultResume(resumeId) {
    try {
        const res = await fetch(`${API_BASE}/resumes/${resumeId}/set-default`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Could not set default resume');
        showToast('Default resume updated! ✅', 'success');
        showMySpaceView();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 8. APPLICATION TIMELINE MODAL ---
async function viewApplicationTimeline(appId) {
    try {
        const res = await fetch(`${API_BASE}/applications/${appId}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Could not load application details');
        const a = await res.json();

        const steps = a.status_timeline || [];
        const statusColors = {
            applied: 'bg-slate-800 text-slate-300',
            under_review: 'bg-indigo-950 text-indigo-300 border border-indigo-700',
            shortlisted: 'bg-amber-950 text-amber-300 border border-amber-700',
            interview: 'bg-purple-950 text-purple-300 border border-purple-700',
            offer: 'bg-emerald-950 text-emerald-300 border border-emerald-700',
            selected: 'bg-emerald-700 text-white font-bold',
            rejected: 'bg-rose-950 text-rose-300 border border-rose-700',
            withdrawn: 'bg-slate-900 text-slate-500'
        };

        const timelineHTML = steps.length ? steps.map((s, idx) => `
            <div class="flex items-start gap-3">
                <div class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${statusColors[s.status] || 'bg-slate-800 text-slate-300'}">
                    ${idx + 1}
                </div>
                <div>
                    <p class="text-xs font-bold text-white capitalize">${(s.status || '').replace(/_/g, ' ')}</p>
                    <p class="text-[10px] text-slate-400">${s.date || s.timestamp || ''}</p>
                    ${s.note ? `<p class="text-[10px] text-slate-300 mt-0.5 italic">"${s.note}"</p>` : ''}
                </div>
            </div>
        `).join('') : `
            <div class="text-center py-4 text-xs text-slate-400">
                <i class="fa-solid fa-clock-rotate-left text-2xl text-indigo-400 mb-2 block"></i>
                <p class="font-bold text-white">Application Submitted</p>
                <p class="mt-1">Status: <span class="capitalize text-indigo-300 font-semibold">${a.status || 'applied'}</span></p>
            </div>
        `;

        const existing = document.getElementById('timeline-modal-dyn');
        if (existing) existing.remove();

        const div = document.createElement('div');
        div.id = 'timeline-modal-dyn';
        div.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm';
        div.innerHTML = `
            <div class="glass-card w-full max-w-md rounded-3xl border border-slate-800 p-6 space-y-4 max-h-[85vh] overflow-y-auto">
                <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div>
                        <h3 class="text-base font-bold text-white">Application Timeline</h3>
                        <p class="text-xs text-slate-400 mt-0.5">${a.opportunity_title || a.job_title || 'Application #' + appId}</p>
                    </div>
                    <button onclick="document.getElementById('timeline-modal-dyn').remove()" class="text-slate-400 hover:text-white">
                        <i class="fa-solid fa-xmark text-lg"></i>
                    </button>
                </div>
                <div class="space-y-3 py-2">
                    ${timelineHTML}
                </div>
                <div class="pt-3 border-t border-slate-800 flex justify-end">
                    <button onclick="document.getElementById('timeline-modal-dyn').remove()" class="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(div);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 9. ORGANIZER: APPLICANT REVIEW & STATUS UPDATE ---
async function viewOppApplicants(oppId) {
    try {
        const res = await fetch(`${API_BASE}/portals/organizer/opportunities/${oppId}/applicants`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Could not load applicant list');
        const data = await res.json();
        const items = data.applicants || (Array.isArray(data) ? data : []);

        const rows = items.length ? items.map(ap => `
            <tr class="border-t border-slate-800 text-xs">
                <td class="p-3 font-semibold text-white">${ap.name || ap.applicant_name || 'Student'}</td>
                <td class="p-3 text-slate-400">${ap.college || '—'}</td>
                <td class="p-3">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                        ap.status === 'selected' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                        ap.status === 'rejected' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                        ap.status === 'shortlisted' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                        'bg-slate-800 text-slate-300'
                    }">${(ap.status || 'applied').replace(/_/g, ' ')}</span>
                </td>
                <td class="p-3 text-slate-400">${ap.applied_at ? ap.applied_at.substring(0, 10) : '—'}</td>
                <td class="p-3">
                    <div class="flex gap-1.5">
                        <button onclick="updateApplicantStatus(${ap.id || ap.application_id}, 'shortlisted', ${oppId})" class="px-2 py-1 rounded bg-amber-900/80 hover:bg-amber-800 text-amber-300 text-[10px] font-semibold transition">Shortlist</button>
                        <button onclick="updateApplicantStatus(${ap.id || ap.application_id}, 'rejected', ${oppId})" class="px-2 py-1 rounded bg-rose-900/80 hover:bg-rose-800 text-rose-300 text-[10px] font-semibold transition">Reject</button>
                    </div>
                </td>
            </tr>
        `).join('') : `<tr><td colspan="5" class="p-6 text-center text-xs text-slate-400">No applicants yet for this opportunity.</td></tr>`;

        const existing = document.getElementById('applicants-modal-dyn');
        if (existing) existing.remove();

        const div = document.createElement('div');
        div.id = 'applicants-modal-dyn';
        div.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm';
        div.innerHTML = `
            <div class="glass-card w-full max-w-2xl rounded-3xl border border-slate-800 p-6 space-y-4 max-h-[85vh] overflow-y-auto">
                <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div>
                        <h3 class="text-base font-bold text-white">Applicants for Opportunity #${oppId}</h3>
                        <p class="text-xs text-slate-400 mt-0.5">${items.length} applicant(s) in review</p>
                    </div>
                    <button onclick="document.getElementById('applicants-modal-dyn').remove()" class="text-slate-400 hover:text-white">
                        <i class="fa-solid fa-xmark text-lg"></i>
                    </button>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                            <tr>
                                <th class="p-3">Student</th>
                                <th class="p-3">College</th>
                                <th class="p-3">Status</th>
                                <th class="p-3">Applied</th>
                                <th class="p-3">Actions</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
                <div class="pt-2 flex justify-end">
                    <button onclick="document.getElementById('applicants-modal-dyn').remove()" class="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(div);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function updateApplicantStatus(appId, status, oppId) {
    try {
        const res = await fetch(`${API_BASE}/portals/recruiter/applications/${appId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({ status: status })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Status update failed');
        showToast(`Application marked as "${status}" ✅`, 'success');
        if (oppId) viewOppApplicants(oppId);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- 10. GLOBAL SEARCH OUTSIDE CLICK LISTENER ---
document.addEventListener('click', function(e) {
    const searchInput   = document.getElementById('global-search-input');
    const searchResults = document.getElementById('global-search-results');
    if (!searchInput || !searchResults) return;
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        hideGlobalSearchResults();
    }
});

// --- 11. LANDING HERO LIVE METRICS & CTA UPDATE ---
async function updateHeroMetrics() {
    try {
        const res = await fetch(`${API_BASE}/portals/admin/dashboard`, {
            headers: state.token ? { 'Authorization': `Bearer ${state.token}` } : {}
        });
        if (!res.ok) return;
        const data = await res.json();
        const m = data.metrics || {};

        const metricEls = document.querySelectorAll('#view-landing .glass-card p.text-2xl');
        if (metricEls.length >= 4) {
            metricEls[0].textContent = (m.total_users || 1054) + '+';
            metricEls[1].textContent = (m.opportunities || 60) + '+';
            metricEls[2].textContent = '0-100';
            metricEls[3].textContent = '100%';
        }
        const metricLabels = document.querySelectorAll('#view-landing .glass-card p.text-xs.text-slate-400');
        if (metricLabels.length >= 2) {
            metricLabels[0].textContent = 'Students Registered';
            metricLabels[1].textContent = 'Active Opportunities';
        }
        const ctaLinks = document.querySelectorAll('#view-landing a[href="#events"]');
        ctaLinks.forEach(link => {
            link.innerHTML = '<i class="fa-solid fa-compass text-indigo-400"></i> Explore Opportunities';
            link.setAttribute('href', '#opportunities');
        });
    } catch (err) {}
}

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(updateHeroMetrics, 1200);
});

// --- 12. ADMIN VERIFICATION QUEUE ---
async function loadAdminVerificationQueue() {
    const container = document.getElementById('admin-verification-queue');
    if (!container) return;
    const mockQueue = [
        { type: 'College Email', name: 'Priya Mehta', detail: 'priya@iitb.ac.in', status: 'pending' },
        { type: 'Company', name: 'TechRocket Pvt Ltd', detail: 'Company size: 200+ employees', status: 'pending' },
        { type: 'Mentor', name: 'Dr. Ananya Singh', detail: 'Ex-Google Staff Engineer', status: 'pending' }
    ];
    container.innerHTML = mockQueue.map(r => `
        <div class="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <div>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950 text-indigo-300 border border-indigo-800 mr-2">${r.type}</span>
                <span class="text-xs font-semibold text-white">${r.name}</span>
                <p class="text-[10px] text-slate-400 mt-0.5">${r.detail}</p>
            </div>
            <div class="flex gap-1.5">
                <button onclick="showToast('Approved ✅', 'success')" class="px-2.5 py-1 rounded-lg bg-emerald-900 hover:bg-emerald-800 text-emerald-300 text-[10px] font-semibold transition">Approve</button>
                <button onclick="showToast('Rejected', 'error')" class="px-2.5 py-1 rounded-lg bg-rose-900 hover:bg-rose-800 text-rose-300 text-[10px] font-semibold transition">Reject</button>
            </div>
        </div>
    `).join('');
}

// Extend showAdminPortalView to render queue
const _existingAdminPortalView = window.showAdminPortalView;
window.showAdminPortalView = async function() {
    if (typeof _existingAdminPortalView === 'function') {
        await _existingAdminPortalView();
    }
    loadAdminVerificationQueue();
};

// --- 13. NOTIFICATION MARK ALL READ ---
async function markAllNotificationsRead() {
    try {
        await fetch(`${API_BASE}/notifications/mark-all-read`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        loadNotifications();
        showToast('All notifications marked as read', 'success');
    } catch (err) {}
}
