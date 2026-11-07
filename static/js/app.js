/**
 * TeamUp by ACE - Frontend Application Controller
 * Handles SPA navigation, authentication, AI match feed, team gap analyzer,
 * team chat polling, icebreaker challenge, and modals.
 */

const API_BASE = '/api';

const state = {
    user: null,
    token: localStorage.getItem('teamup_token') || null,
    events: [],
    currentEvent: null,
    currentEventMatches: [],
    currentTeam: null,
    myTeams: [],
    invites: [],
    activeTab: 'matches',
    chatInterval: null,
    icebreakerTimer: null,
    icebreakerSecondsLeft: 600,
    config: null,
    categories: null,
    browseTeams: { page: 1, pages: 1, total: 0, items: [] },
    browseStudents: { page: 1, pages: 1, total: 0, items: [] },
    recommendedTeams: [],
    profileSkillsMap: {},
    profileRolesSet: new Set(),
    profileInterestsSet: new Set(),
    profileCollabPref: '',
    createTeamSkillsMap: {},
    createTeamRolesSet: new Set(),
    createTeamInterestsSet: new Set()
};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
    await fetchConfig();
    await fetchCategories();
    if (state.token) {
        await fetchCurrentUser();
    }
    updateNavAuthUI();
    await loadEvents();

    // Check hash for routing
    handleHashRouting();
    window.addEventListener('hashchange', handleHashRouting);
});

async function fetchConfig() {
    try {
        const res = await fetch(`${API_BASE}/config`);
        if (res.ok) {
            state.config = await res.json();
            const matcherBadge = document.getElementById('matcher-badge');
            if (matcherBadge && state.config) {
                const isML = state.config.matcher === 'ml';
                matcherBadge.innerHTML = isML 
                    ? `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-900/60 text-purple-300 border border-purple-700/50">
                        <span class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping"></span>
                        🧠 ML Matcher Active
                       </span>`
                    : `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-900/60 text-indigo-300 border border-indigo-700/50">
                        <span class="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                        🎯 Complement Matcher Active
                       </span>`;
            }
        }
    } catch (err) {
        console.error('Config fetch failed:', err);
    }
}

async function fetchCategories() {
    try {
        const res = await fetch(`${API_BASE}/meta/categories`);
        if (res.ok) {
            state.categories = await res.json();
            populateCategoryDropdowns();
        }
    } catch (err) {
        console.error('Failed to load categories:', err);
    }
}

function populateCategoryDropdowns() {
    if (!state.categories) return;
    const cats = state.categories;

    const collegeSelects = ['filter-team-college', 'filter-student-college', 'create-team-college', 'profile-edit-college'];
    collegeSelects.forEach(id => {
        const sel = document.getElementById(id);
        if (sel) {
            const curVal = sel.value;
            sel.innerHTML = `<option value="">${id.includes('create') || id.includes('profile') ? 'Select College' : 'All Colleges'}</option>` +
                cats.colleges.map(c => `<option value="${c}">${c}</option>`).join('');
            if (curVal) sel.value = curVal;
        }
    });

    const skillSelects = ['filter-team-skill', 'filter-student-skill'];
    skillSelects.forEach(id => {
        const sel = document.getElementById(id);
        if (sel) {
            const curVal = sel.value;
            sel.innerHTML = `<option value="">All Required Skills</option>` +
                cats.skills.map(s => `<option value="${s}">${s}</option>`).join('');
            if (curVal) sel.value = curVal;
        }
    });

    const roleSelects = ['filter-team-role', 'filter-student-role'];
    roleSelects.forEach(id => {
        const sel = document.getElementById(id);
        if (sel) {
            const curVal = sel.value;
            sel.innerHTML = `<option value="">All Preferred Roles</option>` +
                cats.preferred_roles.map(r => `<option value="${r}">${r}</option>`).join('');
            if (curVal) sel.value = curVal;
        }
    });

    const collabSelect = document.getElementById('create-team-collab');
    if (collabSelect) {
        collabSelect.innerHTML = `<option value="">Select Working Dynamic</option>` +
            cats.collaboration_preferences.map(cp => `<option value="${cp}">${cp}</option>`).join('');
    }
}

// --- AUTHENTICATION ---
async function fetchCurrentUser() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (res.ok) {
            state.user = await res.json();
        } else {
            logout();
        }
    } catch (err) {
        console.error('Failed to get current user:', err);
        logout();
    }
}

function updateNavAuthUI() {
    const authActions = document.getElementById('auth-actions');
    const userMenu = document.getElementById('user-menu');
    const demoQuickBtn = document.getElementById('demo-quick-btn');

    if (state.user) {
        if (authActions) authActions.classList.add('hidden');
        if (demoQuickBtn) demoQuickBtn.classList.add('hidden');
        if (userMenu) {
            userMenu.classList.remove('hidden');
            document.getElementById('nav-user-name').innerText = state.user.name;
            document.getElementById('nav-user-avatar').src = state.user.avatar_url;
            
            // Reliability pill
            const relBadge = document.getElementById('nav-user-reliability');
            if (relBadge) {
                if (state.user.reliability_score > 0) {
                    relBadge.innerHTML = `<span class="text-emerald-400 font-semibold">${Math.round(state.user.reliability_score)}</span>/100`;
                } else {
                    relBadge.innerHTML = `<span class="text-slate-400">New Member</span>`;
                }
            }

            // Verified checkmark
            const verifiedBadge = document.getElementById('nav-user-verified');
            if (verifiedBadge) {
                verifiedBadge.classList.toggle('hidden', !state.user.is_verified);
            }
        }
    } else {
        if (authActions) authActions.classList.remove('hidden');
        if (demoQuickBtn) demoQuickBtn.classList.remove('hidden');
        if (userMenu) userMenu.classList.add('hidden');
    }
}

async function loginDemoUser() {
    showToast('Logging in as Demo User (Aarav Sharma - MAIT)...', 'info');
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'demo@mait.ac.in', password: 'demo1234' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');

        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('teamup_token', state.token);
        updateNavAuthUI();
        showToast('Welcome back, Aarav! Ready to explore hackathon teams.', 'success');
        
        // Auto open the flagship event detail
        if (state.events.length > 0) {
            window.location.hash = `#event-${state.events[0].id}`;
        } else {
            window.location.hash = '#events';
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');

        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('teamup_token', state.token);
        closeModal('auth-modal');
        updateNavAuthUI();
        showToast(`Welcome, ${state.user.name}!`, 'success');
        handleHashRouting();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const college = document.getElementById('signup-college').value;
    const city = document.getElementById('signup-city').value;
    const year = document.getElementById('signup-year').value;

    try {
        const res = await fetch(`${API_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, college, city, year })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Signup failed');

        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('teamup_token', state.token);
        closeModal('auth-modal');
        updateNavAuthUI();
        showToast(`Account created! ${state.user.is_verified ? 'Verified student badge unlocked!' : ''}`, 'success');
        openProfileModal(); // prompt profile customization
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function logout() {
    state.user = null;
    state.token = null;
    localStorage.removeItem('teamup_token');
    if (state.chatInterval) clearInterval(state.chatInterval);
    updateNavAuthUI();
    showToast('Logged out successfully.', 'info');
    window.location.hash = '#landing';
}

// --- ROUTING & VIEWS ---
function handleHashRouting() {
    const hash = window.location.hash || '#landing';
    hideAllViews();

    if (hash === '#landing' || hash === '') {
        showLandingView();
    } else if (hash === '#events') {
        showEventsView();
    } else if (hash === '#browse-teams') {
        showBrowseTeamsView();
    } else if (hash === '#browse-students') {
        showBrowseStudentsView();
    } else if (hash.startsWith('#event-')) {
        const eventId = parseInt(hash.replace('#event-', ''));
        showEventDetailView(eventId);
    } else if (hash.startsWith('#team-')) {
        const teamId = parseInt(hash.replace('#team-', ''));
        showTeamDashboardView(teamId);
    } else if (hash === '#my-teams') {
        showMyTeamsView();
    } else if (hash === '#invites') {
        openInvitesModal();
    } else {
        showLandingView();
    }
}

function hideAllViews() {
    document.getElementById('view-landing').classList.add('hidden');
    document.getElementById('view-events').classList.add('hidden');
    document.getElementById('view-event-detail').classList.add('hidden');
    document.getElementById('view-team-dashboard').classList.add('hidden');
    document.getElementById('view-my-teams').classList.add('hidden');
    const bTeams = document.getElementById('view-browse-teams');
    if (bTeams) bTeams.classList.add('hidden');
    const bStudents = document.getElementById('view-browse-students');
    if (bStudents) bStudents.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLandingView() {
    document.getElementById('view-landing').classList.remove('hidden');
}

function showEventsView() {
    document.getElementById('view-events').classList.remove('hidden');
    renderEventsList(state.events);
}

// --- EVENTS ---
async function loadEvents() {
    try {
        const res = await fetch(`${API_BASE}/events`);
        if (res.ok) {
            state.events = await res.json();
            renderEventsList(state.events);
        }
    } catch (err) {
        console.error('Failed to load events:', err);
    }
}

function renderEventsList(events) {
    const container = document.getElementById('events-grid');
    if (!container) return;

    if (!events || events.length === 0) {
        container.innerHTML = `
            <div class="col-span-full py-16 text-center text-slate-400 glass-card rounded-2xl">
                <i class="fa-solid fa-calendar-xmark text-4xl mb-3 text-slate-500"></i>
                <p class="text-lg">No events found matching your criteria.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = events.map(e => `
        <div class="glass-card rounded-2xl overflow-hidden flex flex-col group cursor-pointer" onclick="navigateToEvent(${e.id})">
            <div class="relative h-44 overflow-hidden">
                <img src="${e.banner_url}" alt="${e.name}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
                <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent"></div>
                <div class="absolute top-3 left-3 flex flex-wrap gap-1.5">
                    <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-600/90 text-white backdrop-blur">
                        ${e.theme}
                    </span>
                    <span class="px-2.5 py-1 rounded-full text-xs font-medium ${e.mode === 'Online' ? 'bg-emerald-900/80 text-emerald-300' : 'bg-amber-900/80 text-amber-300'} border border-white/10 backdrop-blur">
                        ${e.mode}
                    </span>
                </div>
                <div class="absolute bottom-3 right-3">
                    <span class="px-3 py-1 rounded-full text-xs font-bold bg-amber-400 text-slate-950 shadow-md">
                        🏆 ${e.prize_pool}
                    </span>
                </div>
            </div>

            <div class="p-5 flex-1 flex flex-col justify-between">
                <div>
                    <h3 class="text-xl font-bold text-white group-hover:text-indigo-400 transition">${e.name}</h3>
                    <p class="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                        <i class="fa-regular fa-calendar text-indigo-400"></i> ${e.dates}
                        <span class="text-slate-600">•</span>
                        <i class="fa-solid fa-location-dot text-indigo-400"></i> ${e.city_venue}
                    </p>
                    <p class="text-sm text-slate-300 mt-3 line-clamp-2">${e.tagline || e.description}</p>

                    <div class="mt-4">
                        <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Key Roles Needed:</p>
                        <div class="flex flex-wrap gap-1.5">
                            ${e.required_roles.map(r => `
                                <span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300 border border-slate-700/60">${r}</span>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between">
                    <div class="text-xs text-slate-400 flex items-center gap-3">
                        <span><i class="fa-solid fa-user-group text-slate-500"></i> ${e.teams_count} Teams</span>
                        <span><i class="fa-solid fa-chair text-amber-500"></i> ${e.open_seats_count} Open Seats</span>
                    </div>
                    <button class="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition">
                        Find Teammates <i class="fa-solid fa-arrow-right text-xs"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function filterEvents() {
    const search = document.getElementById('events-search').value.toLowerCase();
    const theme = document.getElementById('events-theme-filter').value;
    const mode = document.getElementById('events-mode-filter').value;

    const filtered = state.events.filter(e => {
        const matchesSearch = !search || e.name.toLowerCase().includes(search) || e.description.toLowerCase().includes(search);
        const matchesTheme = theme === 'All' || e.theme === theme;
        const matchesMode = mode === 'All' || e.mode === mode;
        return matchesSearch && matchesTheme && matchesMode;
    });

    renderEventsList(filtered);
}

function navigateToEvent(eventId) {
    window.location.hash = `#event-${eventId}`;
}

// --- EVENT DETAIL VIEW & TABS ---
async function showEventDetailView(eventId, targetTab = 'matches') {
    document.getElementById('view-event-detail').classList.remove('hidden');

    // Find or fetch event
    state.currentEvent = state.events.find(e => e.id === eventId);
    if (!state.currentEvent) {
        const res = await fetch(`${API_BASE}/events/${eventId}`);
        if (res.ok) state.currentEvent = await res.json();
    }

    if (!state.currentEvent) {
        showToast('Event not found', 'error');
        window.location.hash = '#events';
        return;
    }

    renderEventDetailHeader(state.currentEvent);
    switchEventTab(targetTab);
}

function renderEventDetailHeader(event) {
    document.getElementById('event-detail-banner').src = event.banner_url;
    document.getElementById('event-detail-title').innerText = event.name;
    document.getElementById('event-detail-tagline').innerText = event.tagline || event.description;
    document.getElementById('event-detail-theme').innerText = event.theme;
    document.getElementById('event-detail-mode').innerText = event.mode;
    document.getElementById('event-detail-dates').innerText = event.dates;
    document.getElementById('event-detail-venue').innerText = event.city_venue;
    document.getElementById('event-detail-prize').innerText = event.prize_pool;
    document.getElementById('event-detail-teamsize').innerText = `${event.team_size_min}-${event.team_size_max} Members`;

    const rolesContainer = document.getElementById('event-detail-required-roles');
    rolesContainer.innerHTML = event.required_roles.map(r => `
        <span class="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800/90 text-indigo-300 border border-indigo-900/60">
            ${r}
        </span>
    `).join('');
}

function switchEventTab(tab) {
    state.activeTab = tab;
    const tabBtns = document.querySelectorAll('.event-tab-btn');
    tabBtns.forEach(btn => {
        const active = btn.dataset.tab === tab;
        btn.classList.toggle('text-indigo-400', active);
        btn.classList.toggle('border-indigo-500', active);
        btn.classList.toggle('text-slate-400', !active);
        btn.classList.toggle('border-transparent', !active);
    });

    document.getElementById('tab-content-matches').classList.toggle('hidden', tab !== 'matches');
    document.getElementById('tab-content-seats').classList.toggle('hidden', tab !== 'seats');
    document.getElementById('tab-content-teams').classList.toggle('hidden', tab !== 'teams');

    if (tab === 'matches') loadEventMatches();
    if (tab === 'seats') loadEventSeats();
    if (tab === 'teams') loadEventTeams();
}

// --- AI MATCH FEED (CORE FEATURE) ---
async function loadEventMatches() {
    const container = document.getElementById('matches-grid');
    if (!state.currentEvent) return;

    if (!state.user) {
        container.innerHTML = `
            <div class="col-span-full py-12 text-center glass-card rounded-2xl p-8">
                <i class="fa-solid fa-wand-magic-sparkles text-4xl text-indigo-400 mb-3"></i>
                <h4 class="text-xl font-bold text-white">Log In to See Your AI Matches</h4>
                <p class="text-slate-400 text-sm max-w-md mx-auto mt-2">TeamUp matches your skills against other students to build a full complement team for ${state.currentEvent.name}.</p>
                <div class="mt-5 flex justify-center gap-3">
                    <button onclick="loginDemoUser()" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition">
                        ⚡ Instant Demo Login
                    </button>
                    <button onclick="openModal('auth-modal')" class="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm transition">
                        Sign In / Sign Up
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="col-span-full py-16 text-center text-slate-400">
            <i class="fa-solid fa-spinner fa-spin text-3xl text-indigo-400 mb-3"></i>
            <p class="text-sm font-medium">Running complement-based matching algorithm across candidates...</p>
        </div>
    `;

    // Filters
    const college = document.getElementById('match-filter-college')?.value || 'All';
    const city = document.getElementById('match-filter-city')?.value || 'All';
    const skill = document.getElementById('match-filter-skill')?.value || 'All';
    const experience = document.getElementById('match-filter-experience')?.value || 'All';
    const availability = document.getElementById('match-filter-availability')?.value || 'All';
    const mentorOnly = document.getElementById('match-filter-mentor')?.checked || false;

    const params = new URLSearchParams({
        college, city, skill, experience, availability,
        mentor_only: mentorOnly
    });

    try {
        const res = await fetch(`${API_BASE}/events/${state.currentEvent.id}/matches?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch matches');

        state.currentEventMatches = await res.json();
        renderMatches(state.currentEventMatches);
    } catch (err) {
        container.innerHTML = `
            <div class="col-span-full py-8 text-center text-rose-400 glass-card rounded-2xl">
                <i class="fa-solid fa-triangle-exclamation text-2xl mb-2"></i>
                <p>${err.message}</p>
            </div>
        `;
    }
}

function renderMatches(matches) {
    const container = document.getElementById('matches-grid');
    if (!matches || matches.length === 0) {
        container.innerHTML = `
            <div class="col-span-full py-16 text-center text-slate-400 glass-card rounded-2xl">
                <i class="fa-solid fa-user-slash text-4xl mb-3 text-slate-500"></i>
                <h4 class="text-lg font-bold text-white">No Matching Teammates Found</h4>
                <p class="text-sm mt-1">Try loosening your filter criteria or check back later.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = matches.map(m => {
        const u = m.user;
        const reliabilityDisplay = u.reliability_score > 0
            ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                ⭐ ${Math.round(u.reliability_score)}/100 Reliability
               </span>`
            : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400">
                🌱 New Member
               </span>`;

        const mentorPill = u.is_mentor 
            ? `<span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-950/80 text-purple-300 border border-purple-800/60">🎓 Mentor</span>` 
            : (u.seeking_mentor ? `<span class="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-950/80 text-blue-300 border border-blue-800/60">Seeking Mentor</span>` : '');

        // Complementary skill chips
        const compSkills = m.complementary_skills && m.complementary_skills.length > 0 
            ? m.complementary_skills 
            : u.skills.map(s => s.name).slice(0, 2);

        return `
            <div class="glass-card rounded-2xl p-5 flex flex-col justify-between relative group hover:border-indigo-500/50">
                <div>
                    <!-- Header with Avatar, Info & Match Score -->
                    <div class="flex items-start justify-between gap-3">
                        <div class="flex items-start gap-3">
                            <img src="${u.avatar_url}" alt="${u.name}" class="w-12 h-12 rounded-xl bg-slate-800 p-1 border border-slate-700/80 flex-shrink-0">
                            <div>
                                <div class="flex items-center gap-1.5 flex-wrap">
                                    <h4 class="font-bold text-white text-base hover:text-indigo-400 cursor-pointer" onclick="openPublicProfileModal(${u.id})">${u.name}</h4>
                                    ${u.is_verified ? `<i class="fa-solid fa-circle-check text-emerald-400 text-xs" title="Verified College Student (.edu / .ac.in)"></i>` : ''}
                                    ${mentorPill}
                                </div>
                                <p class="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                                    <i class="fa-solid fa-building-columns text-slate-500 text-[10px]"></i> ${u.college}
                                    <span class="text-slate-600">•</span>
                                    <span>${u.city}</span>
                                </p>
                            </div>
                        </div>

                        <!-- Match % Badge -->
                        <div class="text-right flex-shrink-0">
                            <div class="match-score-pill px-3 py-1 rounded-xl flex items-center gap-1.5 shadow-sm">
                                <i class="fa-solid fa-bolt text-indigo-400 text-xs"></i>
                                <span class="text-base font-extrabold text-indigo-300">${m.score}%</span>
                                <span class="text-[10px] uppercase font-semibold text-indigo-400/80">Match</span>
                            </div>
                            <div class="text-[11px] text-slate-400 mt-1">
                                ${m.workstyle_compatibility}% Work-Style
                            </div>
                        </div>
                    </div>

                    <!-- Reliability & Badges -->
                    <div class="mt-3 flex flex-wrap gap-1.5 items-center">
                        ${reliabilityDisplay}
                        <span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300">
                            <i class="fa-solid fa-clock text-slate-400"></i> ${u.availability}
                        </span>
                        <span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300">
                            <i class="fa-solid fa-bullseye text-slate-400"></i> ${u.goal}
                        </span>
                    </div>

                    <!-- Complementary Skills Banner -->
                    <div class="mt-3.5 p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                        <p class="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 mb-1.5">
                            <i class="fa-solid fa-puzzle-piece"></i> Complementary Skills for Event:
                        </p>
                        <div class="flex flex-wrap gap-1.5">
                            ${compSkills.map(s => `
                                <span class="px-2 py-0.5 rounded text-xs font-medium bg-emerald-950/70 text-emerald-300 border border-emerald-800/60">${s}</span>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Explainable Reason Line -->
                    <div class="mt-3 space-y-1">
                        ${m.reasons.slice(0, 2).map(r => `
                            <p class="text-xs text-slate-300 flex items-start gap-1.5">
                                <span class="text-indigo-400 text-xs mt-0.5">•</span>
                                <span>${r}</span>
                            </p>
                        `).join('')}
                    </div>
                </div>

                <!-- Action CTAs -->
                <div class="mt-5 pt-3.5 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    <button onclick="startIcebreaker(${u.id})" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 hover:text-white text-xs font-medium flex items-center gap-1.5 transition" title="10-minute collaborative mini-task before inviting">
                        <i class="fa-solid fa-stopwatch text-indigo-400"></i> 10-Min Icebreaker
                    </button>
                    <div class="flex items-center gap-1.5">
                        <button onclick="openInviteModal(${u.id}, '${u.name}')" class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow transition">
                            <i class="fa-solid fa-user-plus text-xs"></i> Invite to Team
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// --- OPEN SEATS BOARD ---
async function loadEventSeats() {
    const container = document.getElementById('seats-grid');
    if (!state.currentEvent) return;

    container.innerHTML = `
        <div class="col-span-full py-12 text-center text-slate-400">
            <i class="fa-solid fa-spinner fa-spin text-2xl text-indigo-400"></i>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/events/${state.currentEvent.id}/seats`);
        const seats = await res.json();

        if (!seats || seats.length === 0) {
            container.innerHTML = `
                <div class="col-span-full py-16 text-center text-slate-400 glass-card rounded-2xl">
                    <i class="fa-solid fa-chair text-4xl mb-3 text-slate-500"></i>
                    <h4 class="text-lg font-bold text-white">No Open Seats Posted Yet</h4>
                    <p class="text-sm mt-1">Are you a team lead? Post an open seat to attract specialized talent.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = seats.map(s => `
            <div class="glass-card rounded-2xl p-5 flex flex-col justify-between">
                <div>
                    <div class="flex items-start justify-between">
                        <div>
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-800/60">
                                Open Seat
                            </span>
                            <h4 class="text-lg font-bold text-white mt-1.5">${s.role_title}</h4>
                            <p class="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                                <i class="fa-solid fa-users text-slate-500"></i> Team: <span class="text-indigo-300 font-medium">${s.team_name}</span>
                                <span class="text-slate-600">•</span>
                                <span>Led by ${s.leader_name}</span>
                            </p>
                        </div>
                    </div>

                    <p class="text-sm text-slate-300 mt-3">${s.short_note || 'Looking for an energetic builder to tackle this challenge.'}</p>

                    <div class="mt-4">
                        <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Required Skills:</p>
                        <div class="flex flex-wrap gap-1.5">
                            ${s.required_skills.map(sk => `
                                <span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-indigo-300 border border-slate-700/80">${sk}</span>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="mt-5 pt-3.5 border-t border-slate-800/80 flex items-center justify-between">
                    <span class="text-xs text-slate-400">${s.applications_count} applicants</span>
                    <button onclick="applyToSeat(${s.id}, '${s.role_title}')" class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition">
                        <i class="fa-solid fa-paper-plane text-xs"></i> 1-Tap Apply
                    </button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        showToast('Failed to load open seats', 'error');
    }
}

async function applyToSeat(seatId, roleTitle) {
    if (!state.user) {
        openModal('auth-modal');
        return;
    }

    const note = prompt(`Apply for "${roleTitle}" on this team: Enter a short note or pitch (optional):`, "Hey! I'm experienced with these skills and excited to contribute to this hackathon MVP!");
    if (note === null) return;

    try {
        const res = await fetch(`${API_BASE}/seats/${seatId}/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ note })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Application failed');

        showToast('Application sent to team lead!', 'success');
        loadEventSeats();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function openPostSeatModal() {
    if (!state.user) {
        openModal('auth-modal');
        return;
    }
    if (!state.user.is_verified) {
        showToast('Only verified college students can manage teams & post open seats.', 'warning');
        return;
    }
    openModal('post-seat-modal');
}

async function handlePostSeat(e) {
    e.preventDefault();
    const roleTitle = document.getElementById('seat-role-title').value;
    const skillsRaw = document.getElementById('seat-skills').value;
    const note = document.getElementById('seat-note').value;
    const skills = skillsRaw.split(',').map(s => s.trim()).filter(Boolean);

    // Get current team of user for this event, or prompt creation
    const resTeams = await fetch(`${API_BASE}/teams?event_id=${state.currentEvent.id}&my_teams_only=true`, {
        headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const teams = await resTeams.json();

    let teamId;
    if (teams && teams.length > 0) {
        teamId = teams[0].id;
    } else {
        // Automatically create a team for the user
        const createRes = await fetch(`${API_BASE}/teams`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                event_id: state.currentEvent.id,
                name: `Squad ${state.user.name.split(' ')[0]}`,
                tagline: 'Built on TeamUp',
                leader_role: 'Team Lead'
            })
        });
        const newTeam = await createRes.json();
        teamId = newTeam.id;
    }

    try {
        const res = await fetch(`${API_BASE}/seats`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                team_id: teamId,
                event_id: state.currentEvent.id,
                role_title: roleTitle,
                required_skills: skills,
                short_note: note
            })
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Failed to post open seat');
        }

        closeModal('post-seat-modal');
        showToast('Open seat posted successfully!', 'success');
        loadEventSeats();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- REGISTERED TEAMS ---
async function loadEventTeams() {
    const container = document.getElementById('teams-grid');
    if (!state.currentEvent) return;

    try {
        const res = await fetch(`${API_BASE}/teams?event_id=${state.currentEvent.id}`);
        const teams = await res.json();

        if (!teams || teams.length === 0) {
            container.innerHTML = `
                <div class="col-span-full py-16 text-center text-slate-400 glass-card rounded-2xl">
                    <i class="fa-solid fa-users-slash text-4xl mb-3 text-slate-500"></i>
                    <h4 class="text-lg font-bold text-white">No Teams Formed Yet</h4>
                    <p class="text-sm mt-1">Be the first to create a team for this hackathon!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = teams.map(t => `
            <div class="glass-card rounded-2xl p-5 flex flex-col justify-between cursor-pointer" onclick="navigateToTeam(${t.id})">
                <div>
                    <div class="flex items-start justify-between">
                        <div>
                            <h4 class="text-lg font-bold text-white">${t.name}</h4>
                            <p class="text-xs text-slate-400 mt-0.5">${t.tagline}</p>
                        </div>
                        <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">
                            ${t.members.length} Members
                        </span>
                    </div>

                    ${t.pitch ? `<div class="mt-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800/60 text-xs text-slate-300 italic">"${t.pitch}"</div>` : ''}

                    <div class="mt-4">
                        <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Team Members:</p>
                        <div class="flex flex-wrap gap-2">
                            ${t.members.map(m => `
                                <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/90 border border-slate-700/80">
                                    <img src="${m.user.avatar_url}" class="w-5 h-5 rounded-full">
                                    <span class="text-xs text-slate-200">${m.user.name}</span>
                                    <span class="text-[10px] text-indigo-400">(${m.role})</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="mt-5 pt-3.5 border-t border-slate-800/80 flex items-center justify-end">
                    <button class="px-3.5 py-1.5 rounded-xl bg-indigo-600/90 hover:bg-indigo-600 text-white text-xs font-medium flex items-center gap-1 transition">
                        Open Team Dashboard <i class="fa-solid fa-arrow-right text-xs"></i>
                    </button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        showToast('Failed to load teams', 'error');
    }
}

function navigateToTeam(teamId) {
    window.location.hash = `#team-${teamId}`;
}

// --- TEAM DASHBOARD & GAP ANALYZER ---
async function showTeamDashboardView(teamId) {
    document.getElementById('view-team-dashboard').classList.remove('hidden');

    try {
        // Fetch team details and gap analysis in parallel
        const [teamRes, gapRes] = await Promise.all([
            fetch(`${API_BASE}/teams/${teamId}`),
            fetch(`${API_BASE}/teams/${teamId}/gaps`)
        ]);

        if (!teamRes.ok) throw new Error('Team not found');
        state.currentTeam = await teamRes.json();
        const gapAnalysis = gapRes.ok ? await gapRes.json() : null;

        renderTeamDashboard(state.currentTeam, gapAnalysis);

        // Start chat polling
        if (state.user) {
            loadTeamMessages(teamId);
            if (state.chatInterval) clearInterval(state.chatInterval);
            state.chatInterval = setInterval(() => loadTeamMessages(teamId), 3000);
        }
    } catch (err) {
        showToast(err.message, 'error');
        window.location.hash = '#events';
    }
}

function renderTeamDashboard(team, gaps) {
    document.getElementById('team-dash-name').innerText = team.name;
    document.getElementById('team-dash-tagline').innerText = team.tagline || 'ACE Hackathon Contender';
    document.getElementById('team-dash-event').innerText = team.event_name;

    // AI Team Pitch
    const pitchBox = document.getElementById('team-dash-pitch');
    if (pitchBox) {
        pitchBox.innerText = gaps?.ai_generated_pitch || team.pitch || 'A complementary squad engineered to deliver breakthrough hackathon solutions.';
    }

    // GAP ANALYZER RENDER
    const gapContainer = document.getElementById('team-gap-analyzer-content');
    if (gapContainer && gaps) {
        // Skill Comparison Radar / Bar Chart
        let skillBarsHtml = '';
        if (gaps.skill_comparison && gaps.skill_comparison.length > 0) {
            skillBarsHtml = `
                <div class="space-y-3 mb-4">
                    <p class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                        <i class="fa-solid fa-chart-column text-indigo-400"></i> Skill-Gap Proficiency Radar
                    </p>
                    <div class="space-y-2.5">
                        ${gaps.skill_comparison.map(item => {
                            const curPct = Math.min(100, (item.current_level / 5) * 100);
                            const reqPct = Math.min(100, (item.required_level / 5) * 100);
                            const barColor = item.covered ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 'bg-gradient-to-r from-rose-500 to-amber-500';
                            return `
                                <div class="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                                    <div class="flex items-center justify-between text-xs">
                                        <span class="font-bold text-white">${item.skill}</span>
                                        ${item.covered 
                                            ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">Covered (${item.current_level}/5)</span>`
                                            : `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800">Gap: -${item.gap} (Has: ${item.current_level}, Needs: ${item.required_level})</span>`}
                                    </div>
                                    <div class="space-y-0.5">
                                        <div class="flex justify-between text-[10px] text-slate-400">
                                            <span>Team: Level ${item.current_level}</span>
                                            <span>Min Required: Level ${item.required_level}</span>
                                        </div>
                                        <div class="w-full h-2 rounded-full bg-slate-800 relative overflow-hidden">
                                            <div class="h-full rounded-full ${barColor} transition-all duration-500" style="width: ${curPct}%;"></div>
                                            <div class="absolute top-0 bottom-0 w-1 bg-amber-400 shadow" style="left: calc(${reqPct}% - 2px);" title="Target: Level ${item.required_level}"></div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }

        const missingHtml = (gaps.missing_skills || gaps.missing_roles || []).length > 0 
            ? (gaps.missing_skills || gaps.missing_roles).map(r => `
                <span class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-800/80 flex items-center gap-1.5">
                    <i class="fa-solid fa-circle-exclamation text-rose-400"></i> GAP: ${r}
                </span>
              `).join('')
            : `<span class="text-xs font-medium text-emerald-400 flex items-center gap-1.5">
                <i class="fa-solid fa-circle-check"></i> Complete Coverage! All team requirements met.
               </span>`;

        const coveredHtml = (gaps.covered_skills || gaps.covered_roles || []).map(r => `
            <span class="px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 flex items-center gap-1.5">
                <i class="fa-solid fa-check text-emerald-400"></i> ${r}
            </span>
        `).join('');

        // Suggested candidates to bridge missing roles/skills
        const suggestedHtml = gaps.suggested_candidates && gaps.suggested_candidates.length > 0
            ? `
                <div class="mt-4 pt-4 border-t border-slate-800">
                    <p class="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                        <i class="fa-solid fa-wand-magic-sparkles"></i> AI Suggested Candidates to Bridge Gaps:
                    </p>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        ${gaps.suggested_candidates.map(sc => `
                            <div class="p-3 rounded-xl bg-slate-900/90 border border-indigo-900/40 flex items-center justify-between gap-3">
                                <div class="flex items-center gap-2.5 overflow-hidden">
                                    <img src="${sc.user.avatar_url || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + sc.user.id}" class="w-9 h-9 rounded-lg bg-slate-800 flex-shrink-0">
                                    <div class="truncate">
                                        <div class="flex items-center gap-1">
                                            <span class="text-xs font-bold text-white truncate">${sc.user.name}</span>
                                            <span class="text-[10px] px-1.5 py-0.2 rounded bg-indigo-950 text-indigo-300 font-semibold">${sc.score}%</span>
                                        </div>
                                        <p class="text-[11px] text-emerald-400 font-medium truncate">${sc.reason || 'Bridges gap: ' + sc.role}</p>
                                    </div>
                                </div>
                                <button onclick="openInviteModal(${sc.user.id}, '${sc.user.name.replace(/'/g, "\\'")}', ${team.id}, '${sc.role}')" class="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex-shrink-0 transition">
                                    Invite
                                </button>
                            </div>
                        `).join('')}
                    </div>
                </div>
              `
            : '';

        gapContainer.innerHTML = `
            <div class="space-y-4">
                ${skillBarsHtml}
                <div>
                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Covered Competencies:</p>
                    <div class="flex flex-wrap gap-2">
                        ${coveredHtml}
                    </div>
                </div>
                <div>
                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Remaining Skill Gaps:</p>
                    <div class="flex flex-wrap gap-2">
                        ${missingHtml}
                    </div>
                </div>
                ${suggestedHtml}
            </div>
        `;
    }

    // Load Join Requests for Team Lead
    loadTeamJoinRequests(team.id);

    // Suggested Role Split
    const splitContainer = document.getElementById('team-role-split-list');
    if (splitContainer && gaps?.suggested_role_split) {
        splitContainer.innerHTML = Object.entries(gaps.suggested_role_split).map(([memberName, roleName]) => `
            <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
                <span class="font-semibold text-white flex items-center gap-2">
                    <i class="fa-solid fa-user text-indigo-400"></i> ${memberName}
                </span>
                <span class="px-2.5 py-0.5 rounded-md bg-indigo-950 text-indigo-300 font-medium border border-indigo-900/50">
                    ${roleName}
                </span>
            </div>
        `).join('');
    }

    // Members list
    const membersContainer = document.getElementById('team-members-list');
    if (membersContainer) {
        membersContainer.innerHTML = team.members.map(m => `
            <div class="glass-card rounded-xl p-4 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <img src="${m.user.avatar_url}" class="w-10 h-10 rounded-xl bg-slate-800">
                    <div>
                        <div class="flex items-center gap-1.5">
                            <span class="font-bold text-white text-sm">${m.user.name}</span>
                            ${m.user.id === team.leader_id ? `<span class="px-1.5 py-0.5 rounded text-[10px] bg-amber-950 text-amber-300 border border-amber-800 font-semibold">Lead</span>` : ''}
                        </div>
                        <p class="text-xs text-indigo-400 font-medium">${m.role}</p>
                    </div>
                </div>

                <div class="flex items-center gap-2">
                    <span class="text-xs text-emerald-400 font-semibold">
                        ⭐ ${m.user.reliability_score > 0 ? Math.round(m.user.reliability_score) : 'New'}
                    </span>
                    ${state.user && state.user.id !== m.user.id ? `
                        <button onclick="openFeedbackModal(${team.id}, ${team.event_id}, ${m.user.id}, '${m.user.name}')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 text-xs font-medium transition" title="Submit peer rating & reliability feedback">
                            Rate
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }
}

// --- TEAM CHAT ---
async function loadTeamMessages(teamId) {
    if (!state.token) return;
    try {
        const res = await fetch(`${API_BASE}/teams/${teamId}/messages`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;

        const messages = await res.json();
        const chatContainer = document.getElementById('team-chat-messages');
        if (!chatContainer) return;

        chatContainer.innerHTML = messages.map(m => {
            const isMe = state.user && state.user.id === m.sender_id;
            return `
                <div class="flex gap-2.5 ${isMe ? 'flex-row-reverse' : ''} items-start">
                    <img src="${m.sender_avatar}" class="w-7 h-7 rounded-full bg-slate-800 flex-shrink-0">
                    <div class="max-w-[80%]">
                        <div class="flex items-center gap-2 ${isMe ? 'justify-end' : ''} mb-0.5">
                            <span class="text-[11px] font-semibold text-slate-300">${m.sender_name}</span>
                            <span class="text-[10px] text-slate-500">${new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <div class="px-3.5 py-2 rounded-2xl text-xs ${isMe ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none'}">
                            ${m.content}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        // silent error for polling
    }
}

async function handleSendTeamMessage(e) {
    e.preventDefault();
    if (!state.currentTeam || !state.user) return;
    const input = document.getElementById('team-chat-input');
    const content = input.value.trim();
    if (!content) return;

    try {
        const res = await fetch(`${API_BASE}/teams/${state.currentTeam.id}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ content })
        });
        if (res.ok) {
            input.value = '';
            loadTeamMessages(state.currentTeam.id);
        }
    } catch (err) {
        showToast('Failed to send message', 'error');
    }
}

// --- MY TEAMS VIEW ---
async function showMyTeamsView() {
    document.getElementById('view-my-teams').classList.remove('hidden');
    if (!state.user) {
        loginDemoUser();
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/teams?my_teams_only=true`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const teams = await res.json();
        const container = document.getElementById('my-teams-grid');

        if (!teams || teams.length === 0) {
            container.innerHTML = `
                <div class="col-span-full py-16 text-center text-slate-400 glass-card rounded-2xl">
                    <i class="fa-solid fa-user-group text-4xl mb-3 text-slate-500"></i>
                    <h4 class="text-lg font-bold text-white">You Haven't Joined Any Teams Yet</h4>
                    <p class="text-sm mt-1">Explore hackathons to find complement-matched teammates!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = teams.map(t => `
            <div class="glass-card rounded-2xl p-5 flex flex-col justify-between cursor-pointer" onclick="navigateToTeam(${t.id})">
                <div>
                    <span class="text-xs text-indigo-400 font-semibold uppercase tracking-wider">${t.event_name}</span>
                    <h4 class="text-xl font-bold text-white mt-1">${t.name}</h4>
                    <p class="text-xs text-slate-400 mt-1">${t.tagline}</p>
                    <div class="mt-4 flex flex-wrap gap-2">
                        ${t.members.map(m => `
                            <span class="px-2.5 py-1 rounded-lg bg-slate-800 text-xs text-slate-300">
                                ${m.user.name} (${m.role})
                            </span>
                        `).join('')}
                    </div>
                </div>
                <div class="mt-5 pt-3.5 border-t border-slate-800 flex justify-end">
                    <span class="text-xs font-semibold text-indigo-400 flex items-center gap-1">
                        Go to Dashboard <i class="fa-solid fa-arrow-right"></i>
                    </span>
                </div>
            </div>
        `).join('');
    } catch (err) {
        showToast('Failed to load my teams', 'error');
    }
}

// --- INVITES ---
function openInviteModal(receiverId, receiverName, teamId = null, defaultRole = 'Teammate') {
    if (!state.user) {
        openModal('auth-modal');
        return;
    }
    document.getElementById('invite-receiver-id').value = receiverId;
    document.getElementById('invite-receiver-name').innerText = receiverName;
    document.getElementById('invite-event-id').value = state.currentEvent ? state.currentEvent.id : 1;
    document.getElementById('invite-team-id').value = teamId || '';
    document.getElementById('invite-role').value = defaultRole;
    openModal('invite-modal');
}

async function handleSendInvite(e) {
    e.preventDefault();
    const receiverId = parseInt(document.getElementById('invite-receiver-id').value);
    const eventId = parseInt(document.getElementById('invite-event-id').value);
    const teamIdVal = document.getElementById('invite-team-id').value;
    const teamId = teamIdVal ? parseInt(teamIdVal) : null;
    const role = document.getElementById('invite-role').value;
    const message = document.getElementById('invite-message').value;

    try {
        const res = await fetch(`${API_BASE}/invites`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                receiver_id: receiverId,
                event_id: eventId,
                team_id: teamId,
                proposed_role: role,
                message: message
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to send invite');

        closeModal('invite-modal');
        showToast('Invite sent successfully! 🚀', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function openInvitesModal() {
    if (!state.user) {
        openModal('auth-modal');
        return;
    }
    openModal('invites-modal');
    loadInvites();
}

async function loadInvites() {
    const container = document.getElementById('invites-list');
    container.innerHTML = `<div class="py-8 text-center text-slate-400"><i class="fa-solid fa-spinner fa-spin text-xl text-indigo-400"></i></div>`;

    try {
        const res = await fetch(`${API_BASE}/invites`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const invites = await res.json();

        if (!invites || invites.length === 0) {
            container.innerHTML = `<div class="py-12 text-center text-slate-400"><p>No invitations yet.</p></div>`;
            return;
        }

        container.innerHTML = invites.map(inv => {
            const isReceived = inv.receiver_id === state.user.id;
            return `
                <div class="glass-card rounded-xl p-4 flex flex-col gap-3">
                    <div class="flex items-start justify-between">
                        <div class="flex items-center gap-2.5">
                            <img src="${isReceived ? inv.sender.avatar_url : inv.receiver.avatar_url}" class="w-9 h-9 rounded-lg bg-slate-800">
                            <div>
                                <p class="text-xs text-slate-400">${isReceived ? 'Received from' : 'Sent to'}</p>
                                <h5 class="text-sm font-bold text-white">${isReceived ? inv.sender.name : inv.receiver.name}</h5>
                            </div>
                        </div>
                        <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${
                            inv.status === 'accepted' ? 'bg-emerald-950 text-emerald-300' : 
                            (inv.status === 'declined' ? 'bg-rose-950 text-rose-300' : 'bg-amber-950 text-amber-300')
                        }">
                            ${inv.status.toUpperCase()}
                        </span>
                    </div>

                    <div class="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg">
                        <p class="font-semibold text-indigo-400 mb-0.5">${inv.event_name} • Role: ${inv.proposed_role}</p>
                        <p class="italic">"${inv.message}"</p>
                    </div>

                    ${isReceived && inv.status === 'pending' ? `
                        <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
                            <button onclick="respondInvite(${inv.id}, 'declined')" class="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition">
                                Decline
                            </button>
                            <button onclick="respondInvite(${inv.id}, 'accepted')" class="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition">
                                Accept & Join Team
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    } catch (err) {
        showToast('Failed to load invites', 'error');
    }
}

async function respondInvite(inviteId, status) {
    try {
        const res = await fetch(`${API_BASE}/invites/${inviteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to update invite');

        showToast(`Invite ${status}!`, 'success');
        loadInvites();
        if (status === 'accepted' && data.team_id) {
            closeModal('invites-modal');
            navigateToTeam(data.team_id);
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- ICEBREAKER CHALLENGE (10-MIN COLLABORATION MINI-TASK) ---
async function startIcebreaker(partnerId) {
    if (!state.user) {
        openModal('auth-modal');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/icebreaker/${partnerId}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Failed to start icebreaker');

        const data = await res.json();
        renderIcebreakerModal(data);
        openModal('icebreaker-modal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderIcebreakerModal(data) {
    document.getElementById('icebreaker-partner-avatar').src = data.partner.avatar_url;
    document.getElementById('icebreaker-partner-name').innerText = data.partner.name;
    document.getElementById('icebreaker-partner-college').innerText = data.partner.college;

    document.getElementById('icebreaker-compat-score').innerText = `${data.workstyle_analysis.overall_compatibility}%`;
    document.getElementById('icebreaker-compat-role').innerText = data.workstyle_analysis.role_synergy.description;
    document.getElementById('icebreaker-compat-sched').innerText = data.workstyle_analysis.schedule.description;

    document.getElementById('icebreaker-task-title').innerText = data.prompt.title;
    document.getElementById('icebreaker-task-scenario').innerText = data.prompt.scenario;
    document.getElementById('icebreaker-task-instruction').innerText = data.prompt.task;
    document.getElementById('icebreaker-task-deliverable').innerText = data.prompt.deliverable;

    // Reset countdown timer
    state.icebreakerSecondsLeft = 600;
    updateIcebreakerTimerDisplay();
    if (state.icebreakerTimer) clearInterval(state.icebreakerTimer);
    state.icebreakerTimer = setInterval(() => {
        if (state.icebreakerSecondsLeft > 0) {
            state.icebreakerSecondsLeft--;
            updateIcebreakerTimerDisplay();
        } else {
            clearInterval(state.icebreakerTimer);
            showToast('⏰ 10-Minute Icebreaker completed! Time to form your team.', 'info');
        }
    }, 1000);

    // Set partner invite button
    const sendInviteBtn = document.getElementById('icebreaker-invite-btn');
    if (sendInviteBtn) {
        sendInviteBtn.onclick = () => {
            closeModal('icebreaker-modal');
            openInviteModal(data.partner.id, data.partner.name);
        };
    }
}

function updateIcebreakerTimerDisplay() {
    const minutes = Math.floor(state.icebreakerSecondsLeft / 60);
    const seconds = state.icebreakerSecondsLeft % 60;
    const timerElem = document.getElementById('icebreaker-timer');
    if (timerElem) {
        timerElem.innerText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// --- PEER FEEDBACK & RELIABILITY ---
function openFeedbackModal(teamId, eventId, toUserId, toUserName) {
    document.getElementById('feedback-team-id').value = teamId;
    document.getElementById('feedback-event-id').value = eventId;
    document.getElementById('feedback-target-user-id').value = toUserId;
    document.getElementById('feedback-target-name').innerText = toUserName;
    openModal('feedback-modal');
}

async function handleSubmitFeedback(e) {
    e.preventDefault();
    const teamId = parseInt(document.getElementById('feedback-team-id').value);
    const eventId = parseInt(document.getElementById('feedback-event-id').value);
    const toUserId = parseInt(document.getElementById('feedback-target-user-id').value);
    const rating = parseInt(document.querySelector('input[name="feedback-rating"]:checked')?.value || '5');
    const comment = document.getElementById('feedback-comment').value;

    const tags = Array.from(document.querySelectorAll('input[name="feedback-tags"]:checked')).map(el => el.value);

    try {
        const res = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                team_id: teamId,
                event_id: eventId,
                to_user_id: toUserId,
                rating,
                tags,
                comment
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Feedback submission failed');

        closeModal('feedback-modal');
        showToast('Peer feedback submitted! Reliability score updated.', 'success');
        showTeamDashboardView(teamId);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- PROFILE VIEW & EDIT ---
async function openProfileModal() {
    if (!state.user) {
        openModal('auth-modal');
        return;
    }
    const u = state.user;
    document.getElementById('profile-edit-name').value = u.name || '';
    document.getElementById('profile-edit-college').value = u.college || '';
    document.getElementById('profile-edit-city').value = u.city || '';
    document.getElementById('profile-edit-year').value = u.year || '';
    document.getElementById('profile-edit-bio').value = u.bio || u.short_bio || '';
    document.getElementById('profile-edit-exp').value = u.experience_level || 'Intermediate';
    document.getElementById('profile-edit-past-hackathons').value = u.past_hackathons_count || 0;
    document.getElementById('profile-edit-avail').value = u.availability || 'Full-time';
    document.getElementById('profile-edit-team-size').value = u.preferred_team_size || 4;
    document.getElementById('profile-edit-mentor').checked = !!u.is_mentor;
    document.getElementById('profile-edit-seeking-mentor').checked = !!u.seeking_mentor;

    renderProfileSkillsGrouped();
    renderProfileRolesPicker();
    renderProfileInterestsPicker();
    renderProfileCollabCards();

    openModal('profile-modal');
}

function renderProfileSkillsGrouped() {
    const container = document.getElementById('profile-skills-grouped-container');
    if (!container || !state.categories) return;

    const userProf = state.user?.skill_proficiency || {};
    state.profileSkillsMap = { ...userProf };

    // Also support array skills
    if (state.user?.skills && Array.isArray(state.user.skills)) {
        state.user.skills.forEach(s => {
            const skillName = typeof s === 'string' ? s : s.name;
            if (!(skillName in state.profileSkillsMap)) {
                state.profileSkillsMap[skillName] = typeof s === 'object' && s.level ? parseInt(s.level) || 3 : 3;
            }
        });
    }

    const groups = state.categories.skill_groups || {};
    container.innerHTML = Object.entries(groups).map(([groupName, skills]) => `
        <div class="space-y-1.5 pb-2.5 border-b border-slate-800/80 last:border-0">
            <span class="text-[11px] font-bold text-indigo-400 uppercase tracking-wider block">${groupName}</span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                ${skills.map(skill => {
                    const hasSkill = skill in state.profileSkillsMap;
                    const level = state.profileSkillsMap[skill] || 3;
                    const safeKey = skill.replace(/[^a-zA-Z0-9]/g, '_');
                    return `
                        <div class="p-2 rounded-lg bg-slate-950/80 border ${hasSkill ? 'border-indigo-600' : 'border-slate-800'} flex flex-col gap-1 transition" id="prof-skill-card-${safeKey}">
                            <div class="flex items-center justify-between">
                                <label class="flex items-center gap-1.5 cursor-pointer text-xs ${hasSkill ? 'text-white font-bold' : 'text-slate-400'}">
                                    <input type="checkbox" onchange="toggleProfileSkill('${skill}', this.checked)" ${hasSkill ? 'checked' : ''} class="rounded text-indigo-600 bg-slate-900 border-slate-700">
                                    <span>${skill}</span>
                                </label>
                                <span class="text-[10px] font-semibold text-amber-400" id="prof-skill-level-lbl-${safeKey}">
                                    ${hasSkill ? 'Level ' + level + '/5' : ''}
                                </span>
                            </div>
                            <div class="${hasSkill ? '' : 'hidden'} pt-1" id="prof-skill-slider-wrap-${safeKey}">
                                <input type="range" min="1" max="5" value="${level}" oninput="setProfileSkillLevel('${skill}', this.value)" class="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500">
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `).join('');
}

function toggleProfileSkill(skill, isChecked) {
    const safeKey = skill.replace(/[^a-zA-Z0-9]/g, '_');
    const wrap = document.getElementById(`prof-skill-slider-wrap-${safeKey}`);
    const lbl = document.getElementById(`prof-skill-level-lbl-${safeKey}`);
    const card = document.getElementById(`prof-skill-card-${safeKey}`);

    if (isChecked) {
        state.profileSkillsMap[skill] = state.profileSkillsMap[skill] || 3;
        if (wrap) wrap.classList.remove('hidden');
        if (lbl) lbl.innerText = `Level ${state.profileSkillsMap[skill]}/5`;
        if (card) {
            card.classList.remove('border-slate-800');
            card.classList.add('border-indigo-600');
        }
    } else {
        delete state.profileSkillsMap[skill];
        if (wrap) wrap.classList.add('hidden');
        if (lbl) lbl.innerText = '';
        if (card) {
            card.classList.remove('border-indigo-600');
            card.classList.add('border-slate-800');
        }
    }
}

function setProfileSkillLevel(skill, val) {
    const level = parseInt(val) || 1;
    state.profileSkillsMap[skill] = level;
    const safeKey = skill.replace(/[^a-zA-Z0-9]/g, '_');
    const lbl = document.getElementById(`prof-skill-level-lbl-${safeKey}`);
    if (lbl) lbl.innerText = `Level ${level}/5`;
}

function renderProfileRolesPicker() {
    const container = document.getElementById('profile-roles-container');
    if (!container || !state.categories) return;
    state.profileRolesSet = new Set(state.user?.preferred_roles || []);

    container.innerHTML = state.categories.preferred_roles.map(role => {
        const isSelected = state.profileRolesSet.has(role);
        return `
            <button type="button" onclick="toggleProfileRole('${role}', this)" class="px-2.5 py-1 rounded-lg text-xs font-medium border transition ${isSelected ? 'bg-purple-950 text-purple-200 border-purple-600' : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'}">
                ${role}
            </button>
        `;
    }).join('');
}

function toggleProfileRole(role, btn) {
    if (state.profileRolesSet.has(role)) {
        state.profileRolesSet.delete(role);
        btn.className = 'px-2.5 py-1 rounded-lg text-xs font-medium border transition bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700';
    } else {
        state.profileRolesSet.add(role);
        btn.className = 'px-2.5 py-1 rounded-lg text-xs font-medium border transition bg-purple-950 text-purple-200 border-purple-600';
    }
}

function renderProfileInterestsPicker() {
    const container = document.getElementById('profile-interests-container');
    if (!container || !state.categories) return;
    state.profileInterestsSet = new Set(state.user?.interests || []);

    container.innerHTML = state.categories.interests.map(interest => {
        const isSelected = state.profileInterestsSet.has(interest);
        return `
            <button type="button" onclick="toggleProfileInterest('${interest}', this)" class="px-2.5 py-1 rounded-lg text-xs font-medium border transition ${isSelected ? 'bg-amber-950 text-amber-200 border-amber-600' : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'}">
                ${interest}
            </button>
        `;
    }).join('');
}

function toggleProfileInterest(interest, btn) {
    if (state.profileInterestsSet.has(interest)) {
        state.profileInterestsSet.delete(interest);
        btn.className = 'px-2.5 py-1 rounded-lg text-xs font-medium border transition bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700';
    } else {
        state.profileInterestsSet.add(interest);
        btn.className = 'px-2.5 py-1 rounded-lg text-xs font-medium border transition bg-amber-950 text-amber-200 border-amber-600';
    }
}

function renderProfileCollabCards() {
    const container = document.getElementById('profile-collab-cards-container');
    if (!container || !state.categories) return;
    state.profileCollabPref = state.user?.collaboration_preference || '';

    container.innerHTML = state.categories.collaboration_preferences.map(sentence => {
        const isSelected = state.profileCollabPref === sentence;
        return `
            <div onclick="selectProfileCollab('${sentence.replace(/'/g, "\\'")}', this)" class="p-2.5 rounded-xl border text-xs cursor-pointer transition flex items-start gap-2 ${isSelected ? 'bg-emerald-950/60 border-emerald-500 text-white font-medium' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'}">
                <i class="fa-solid fa-check-circle mt-0.5 ${isSelected ? 'text-emerald-400' : 'text-slate-600'}"></i>
                <span class="leading-snug">${sentence}</span>
            </div>
        `;
    }).join('');
}

function selectProfileCollab(sentence, el) {
    state.profileCollabPref = sentence;
    const cards = document.getElementById('profile-collab-cards-container')?.children || [];
    for (const card of cards) {
        card.className = 'p-2.5 rounded-xl border text-xs cursor-pointer transition flex items-start gap-2 bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700';
        const icon = card.querySelector('i');
        if (icon) icon.className = 'fa-solid fa-check-circle mt-0.5 text-slate-600';
    }
    el.className = 'p-2.5 rounded-xl border text-xs cursor-pointer transition flex items-start gap-2 bg-emerald-950/60 border-emerald-500 text-white font-medium';
    const icon = el.querySelector('i');
    if (icon) icon.className = 'fa-solid fa-check-circle mt-0.5 text-emerald-400';
}

async function handleProfileSave(e) {
    e.preventDefault();

    const selectedSkills = Object.keys(state.profileSkillsMap);
    const skillProficiency = { ...state.profileSkillsMap };
    const preferredRoles = Array.from(state.profileRolesSet);
    const interests = Array.from(state.profileInterestsSet);

    const updatePayload = {
        name: document.getElementById('profile-edit-name').value,
        college: document.getElementById('profile-edit-college').value,
        city: document.getElementById('profile-edit-city').value,
        year: document.getElementById('profile-edit-year').value,
        bio: document.getElementById('profile-edit-bio').value,
        experience_level: document.getElementById('profile-edit-exp').value,
        availability: document.getElementById('profile-edit-avail').value,
        preferred_team_size: parseInt(document.getElementById('profile-edit-team-size').value || '4'),
        past_hackathons_count: parseInt(document.getElementById('profile-edit-past-hackathons').value || '0'),
        collaboration_preference: state.profileCollabPref,
        skills: selectedSkills,
        skill_proficiency: skillProficiency,
        preferred_roles: preferredRoles,
        interests: interests,
        is_mentor: document.getElementById('profile-edit-mentor').checked,
        seeking_mentor: document.getElementById('profile-edit-seeking-mentor').checked
    };

    try {
        const res = await fetch(`${API_BASE}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify(updatePayload)
        });
        const updated = await res.json();
        if (!res.ok) throw new Error(updated.detail || 'Profile update failed');

        state.user = updated;
        updateNavAuthUI();
        closeModal('profile-modal');
        showToast('Profile updated! Matching engine adjusted.', 'success');
        if (window.location.hash === '#browse-teams') {
            loadRecommendedTeams();
        }
        if (state.currentEvent) loadEventMatches();
    } catch (err) {
        showToast(err.message, 'error');
    }
}
}

async function openPublicProfileModal(userId) {
    try {
        const res = await fetch(`${API_BASE}/profile/${userId}`);
        if (!res.ok) throw new Error('User not found');
        const u = await res.json();

        document.getElementById('pub-profile-avatar').src = u.avatar_url;
        document.getElementById('pub-profile-name').innerText = u.name;
        document.getElementById('pub-profile-college').innerText = u.college;
        document.getElementById('pub-profile-city').innerText = `${u.city} • ${u.year}`;
        document.getElementById('pub-profile-bio').innerText = u.short_bio || 'Hackathon builder on TeamUp.';
        document.getElementById('pub-profile-score').innerText = u.reliability_score > 0 ? `${Math.round(u.reliability_score)}/100` : 'New Member';
        document.getElementById('pub-profile-verified').classList.toggle('hidden', !u.is_verified);

        document.getElementById('pub-profile-skills').innerHTML = u.skills.map(s => `
            <span class="px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-indigo-300 border border-slate-700/80">
                ${s.name} <span class="text-[10px] text-slate-400">(${s.level})</span>
            </span>
        `).join('');

        document.getElementById('pub-profile-interests').innerHTML = (u.interests || []).map(i => `
            <span class="px-2.5 py-1 rounded-lg text-xs bg-purple-950/60 text-purple-300 border border-purple-900/50">${i}</span>
        `).join('');

        // Action buttons
        document.getElementById('pub-profile-icebreaker-btn').onclick = () => {
            closeModal('public-profile-modal');
            startIcebreaker(u.id);
        };
        document.getElementById('pub-profile-invite-btn').onclick = () => {
            closeModal('public-profile-modal');
            openInviteModal(u.id, u.name);
        };
        document.getElementById('pub-profile-report-btn').onclick = () => {
            openReportModal(u.id, u.name);
        };

        openModal('public-profile-modal');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- SAFETY: REPORT & BLOCK ---
function openReportModal(userId, userName) {
    document.getElementById('report-user-id').value = userId;
    document.getElementById('report-user-name').innerText = userName;
    openModal('report-modal');
}

async function handleReportSubmit(e) {
    e.preventDefault();
    const userId = parseInt(document.getElementById('report-user-id').value);
    const reason = document.getElementById('report-reason').value;
    const details = document.getElementById('report-details').value;

    try {
        const res = await fetch(`${API_BASE}/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ reported_user_id: userId, reason, details })
        });
        const data = await res.json();
        closeModal('report-modal');
        showToast(data.message, 'info');
    } catch (err) {
        showToast('Report could not be delivered', 'error');
    }
}

async function handleBlockUser(userId) {
    if (!confirm('Are you sure you want to block this user? They will not appear in your match feed.')) return;
    try {
        const res = await fetch(`${API_BASE}/block`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await res.json();
        closeModal('public-profile-modal');
        showToast(data.message, 'info');
        if (state.currentEvent) loadEventMatches();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- MODAL UTILITIES ---
function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
    if (id === 'icebreaker-modal' && state.icebreakerTimer) {
        clearInterval(state.icebreakerTimer);
    }
}

// --- TOAST NOTIFICATIONS ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const colors = {
        success: 'bg-emerald-950/90 text-emerald-200 border-emerald-700/80',
        error: 'bg-rose-950/90 text-rose-200 border-rose-700/80',
        warning: 'bg-amber-950/90 text-amber-200 border-amber-700/80',
        info: 'bg-indigo-950/90 text-indigo-200 border-indigo-700/80'
    };
    const icons = {
        success: 'fa-circle-check text-emerald-400',
        error: 'fa-circle-xmark text-rose-400',
        warning: 'fa-triangle-exclamation text-amber-400',
        info: 'fa-circle-info text-indigo-400'
    };

    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur shadow-2xl text-xs font-medium animate-fade-in ${colors[type] || colors.info}`;
    toast.innerHTML = `
        <i class="fa-solid ${icons[type] || icons.info} text-sm"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// =========================================================================
// --- BROWSE TEAMS, BROWSE STUDENTS, JOIN REQUESTS, CREATE TEAM ---
// =========================================================================

// --- BROWSE TEAMS ---
let teamSearchDebounce = null;
function debounceTeamSearch() {
    clearTimeout(teamSearchDebounce);
    teamSearchDebounce = setTimeout(() => {
        state.browseTeams.page = 1;
        loadBrowseTeams(1);
    }, 300);
}

function applyTeamFilters() {
    state.browseTeams.page = 1;
    loadBrowseTeams(1);
}

function resetTeamFilters() {
    const s = document.getElementById('filter-team-search'); if (s) s.value = '';
    const c = document.getElementById('filter-team-college'); if (c) c.value = '';
    const sk = document.getElementById('filter-team-skill'); if (sk) sk.value = '';
    const r = document.getElementById('filter-team-role'); if (r) r.value = '';
    const a = document.getElementById('filter-team-avail'); if (a) a.value = '';
    const e = document.getElementById('filter-team-exp'); if (e) e.value = '';
    const v = document.getElementById('filter-team-vacancies'); if (v) v.checked = true;
    state.browseTeams.page = 1;
    loadBrowseTeams(1);
}

async function showBrowseTeamsView() {
    document.getElementById('view-browse-teams').classList.remove('hidden');
    loadRecommendedTeams();
    loadBrowseTeams(state.browseTeams.page || 1);
}

async function loadRecommendedTeams() {
    const container = document.getElementById('recommended-teams-carousel');
    if (!container) return;
    if (!state.token) {
        container.innerHTML = `<div class="text-xs text-slate-400 py-4 text-center col-span-3">
            <button onclick="loginDemoUser()" class="text-amber-400 underline font-semibold">Sign in</button> to view AI-matched teams tailored to your profile.
        </div>`;
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/me/recommended-teams?per_page=3`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) return;
        const data = await res.json();
        state.recommendedTeams = data.items || [];
        renderRecommendedTeamsList(state.recommendedTeams);
    } catch (err) {
        console.error('Failed to load recommended teams:', err);
    }
}

function renderRecommendedTeamsList(items) {
    const container = document.getElementById('recommended-teams-carousel');
    if (!container) return;
    if (items.length === 0) {
        container.innerHTML = `<div class="text-xs text-slate-400 py-3 text-center col-span-3">No recommended teams found for your current skills.</div>`;
        return;
    }

    container.innerHTML = items.map(match => {
        const t = match.team;
        const scoreColor = match.score >= 80 ? 'from-emerald-600 to-teal-600' : (match.score >= 60 ? 'from-indigo-600 to-purple-600' : 'from-amber-600 to-orange-600');
        const reasonsHtml = (match.reasons || []).slice(0, 2).map(r => `
            <p class="text-[11px] text-indigo-300 leading-snug"><i class="fa-solid fa-sparkles text-amber-400 mr-1"></i>${r}</p>
        `).join('');

        const reqSkillsHtml = (t.required_skills || []).slice(0, 4).map(s => `
            <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">${s}</span>
        `).join('');

        return `
            <div class="glass-card rounded-xl p-4 border border-indigo-800/60 flex flex-col justify-between space-y-3 relative overflow-hidden">
                <div class="space-y-2">
                    <div class="flex items-center justify-between gap-1.5">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r ${scoreColor} text-white shadow-sm">
                            ${match.score}% Match
                        </span>
                        <span class="text-[10px] text-emerald-400 font-semibold">${t.vacancies} open</span>
                    </div>
                    <div>
                        <h4 class="text-sm font-black text-white hover:text-indigo-400 cursor-pointer" onclick="navigateToTeam(${t.id})">${t.team_name || t.name}</h4>
                        <p class="text-[11px] text-slate-400 truncate">${t.college}</p>
                    </div>

                    <div class="space-y-1 bg-slate-900/70 p-2 rounded-lg border border-slate-800">
                        ${reasonsHtml}
                    </div>

                    <div class="space-y-1">
                        <p class="text-[10px] font-semibold text-slate-400 uppercase">Needs Skills:</p>
                        <div class="flex flex-wrap gap-1">
                            ${reqSkillsHtml}
                        </div>
                    </div>
                </div>

                <div class="flex items-center justify-between pt-2 border-t border-slate-800">
                    <button onclick="navigateToTeam(${t.id})" class="text-xs text-slate-400 hover:text-white transition">Details</button>
                    <button onclick="requestJoinTeam(${t.id})" class="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition flex items-center gap-1">
                        <i class="fa-solid fa-paper-plane text-[10px]"></i> Apply
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

async function loadBrowseTeams(page = 1) {
    const container = document.getElementById('teams-browse-grid');
    if (!container) return;
    container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400 text-xs"><i class="fa-solid fa-circle-notch fa-spin text-lg text-indigo-500 mb-2 block"></i> Loading teams...</div>`;

    const search = document.getElementById('filter-team-search')?.value || '';
    const college = document.getElementById('filter-team-college')?.value || '';
    const skill = document.getElementById('filter-team-skill')?.value || '';
    const role = document.getElementById('filter-team-role')?.value || '';
    const avail = document.getElementById('filter-team-avail')?.value || '';
    const exp = document.getElementById('filter-team-exp')?.value || '';
    const vacanciesOnly = document.getElementById('filter-team-vacancies')?.checked !== false;

    const params = new URLSearchParams({
        page: page,
        per_page: 18,
        vacancies_gt_0: vacanciesOnly
    });
    if (search) params.append('skill', search);
    if (college) params.append('college', college);
    if (skill) params.append('skill', skill);
    if (role) params.append('role', role);
    if (avail) params.append('availability', avail);
    if (exp) params.append('experience', exp);

    try {
        const res = await fetch(`${API_BASE}/teams/browse?${params.toString()}`);
        if (!res.ok) throw new Error('Failed to load teams');
        const data = await res.json();
        state.browseTeams = data;
        renderBrowseTeamsList(data);
        renderPagination('teams-pagination', data.page, data.pages, loadBrowseTeams);
    } catch (err) {
        container.innerHTML = `<div class="col-span-3 text-center py-8 text-rose-400 text-xs">${err.message}</div>`;
    }
}

function renderBrowseTeamsList(data) {
    const container = document.getElementById('teams-browse-grid');
    if (!container) return;
    if (data.items.length === 0) {
        container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400 text-xs">No teams match your filter criteria. Try broadening your search.</div>`;
        return;
    }

    container.innerHTML = data.items.map(team => {
        const skillsChips = (team.required_skills || []).slice(0, 4).map(s => {
            const minLvl = (team.skill_requirements && team.skill_requirements[s]) ? `L${team.skill_requirements[s]}` : '';
            return `<span class="px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-950/70 text-indigo-300 border border-indigo-800/60">${s} ${minLvl ? '<span class="text-amber-400 font-bold ml-0.5">' + minLvl + '</span>' : ''}</span>`;
        }).join('');

        const rolesChips = (team.preferred_roles || []).slice(0, 2).map(r => `
            <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-950/70 text-purple-300 border border-purple-800/60">${r}</span>
        `).join('');

        const totalSlots = (team.current_team_size || 1) + (team.vacancies || 0);

        return `
            <div class="glass-card rounded-2xl p-5 border-slate-800 hover:border-indigo-600/60 transition flex flex-col justify-between space-y-4">
                <div class="space-y-3">
                    <div class="flex items-start justify-between gap-2">
                        <div>
                            <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider">${team.team_id || 'TEAM'}</span>
                            <h3 class="text-base font-bold text-white hover:text-indigo-400 cursor-pointer" onclick="navigateToTeam(${team.id})">${team.team_name || team.name}</h3>
                            <p class="text-xs text-indigo-300/80 mt-0.5 truncate max-w-[220px]"><i class="fa-solid fa-building-columns text-[10px] mr-1"></i>${team.college}</p>
                        </div>
                        <span class="px-2.5 py-1 rounded-full text-[11px] font-bold ${team.vacancies > 0 ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-800 text-slate-400'}">
                            ${team.vacancies > 0 ? team.vacancies + ' open' : 'Full'}
                        </span>
                    </div>

                    ${team.team_description ? `<p class="text-xs text-slate-300 line-clamp-2 italic">${team.team_description}</p>` : ''}

                    <div class="space-y-1.5">
                        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Required Skills (Min Level):</p>
                        <div class="flex flex-wrap gap-1">
                            ${skillsChips || '<span class="text-[10px] text-slate-500">None specified</span>'}
                        </div>
                    </div>

                    ${rolesChips ? `
                    <div class="space-y-1">
                        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Hiring Roles:</p>
                        <div class="flex flex-wrap gap-1">${rolesChips}</div>
                    </div>` : ''}

                    <div class="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
                        <span><i class="fa-solid fa-clock mr-1 text-slate-500"></i>${team.availability}</span>
                        <span><i class="fa-solid fa-users mr-1 text-slate-500"></i>${team.current_team_size}/${totalSlots} members</span>
                    </div>
                </div>

                <div class="flex items-center justify-between pt-3 border-t border-slate-800 gap-2">
                    <button onclick="navigateToTeam(${team.id})" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition font-medium">
                        View Team
                    </button>
                    ${team.vacancies > 0 ? `
                        <button onclick="requestJoinTeam(${team.id})" class="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition flex items-center gap-1">
                            <i class="fa-solid fa-user-plus text-[10px]"></i> Join Team
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

async function requestJoinTeam(teamId) {
    if (!state.token) {
        showToast('Please sign in or use Demo Login to apply.', 'warning');
        openModal('auth-modal');
        return;
    }

    const note = prompt('Add a quick message to the team lead (optional):', 'Hey! I would love to join your squad for the hackathon.');
    if (note === null) return;

    try {
        const res = await fetch(`${API_BASE}/teams/${teamId}/join-request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ message: note || 'Interested in joining your team!' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Join request failed');
        showToast('Application submitted to team lead!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- BROWSE STUDENTS ---
let studentSearchDebounce = null;
function debounceStudentSearch() {
    clearTimeout(studentSearchDebounce);
    studentSearchDebounce = setTimeout(() => {
        state.browseStudents.page = 1;
        loadBrowseStudents(1);
    }, 300);
}

function applyStudentFilters() {
    state.browseStudents.page = 1;
    loadBrowseStudents(1);
}

function resetStudentFilters() {
    const s = document.getElementById('filter-student-search'); if (s) s.value = '';
    const c = document.getElementById('filter-student-college'); if (c) c.value = '';
    const sk = document.getElementById('filter-student-skill'); if (sk) sk.value = '';
    const r = document.getElementById('filter-student-role'); if (r) r.value = '';
    const a = document.getElementById('filter-student-avail'); if (a) a.value = '';
    const e = document.getElementById('filter-student-exp'); if (e) e.value = '';
    const g = document.getElementById('filter-student-gap-team'); if (g) g.value = '';
    state.browseStudents.page = 1;
    loadBrowseStudents(1);
}

async function showBrowseStudentsView() {
    document.getElementById('view-browse-students').classList.remove('hidden');
    loadBrowseStudents(state.browseStudents.page || 1);
    populateTeamGapSelect();
}

async function populateTeamGapSelect() {
    const sel = document.getElementById('filter-student-gap-team');
    if (!sel || !state.token) return;
    try {
        const res = await fetch(`${API_BASE}/teams?my_teams_only=true`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (res.ok) {
            const teams = await res.json();
            sel.innerHTML = '<option value="">Fills My Team\'s Gaps (Select Team)</option>' +
                teams.map(t => `<option value="${t.id}">Fills gap for: ${t.team_name || t.name}</option>`).join('');
        }
    } catch (err) {
        console.error(err);
    }
}

async function loadBrowseStudents(page = 1) {
    const container = document.getElementById('students-browse-grid');
    if (!container) return;
    container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400 text-xs"><i class="fa-solid fa-circle-notch fa-spin text-lg text-purple-500 mb-2 block"></i> Loading talent pool...</div>`;

    if (!state.token) {
        container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400 text-xs">
            <button onclick="loginDemoUser()" class="text-amber-400 underline font-semibold">Sign in</button> to browse verified students and recruit teammates.
        </div>`;
        return;
    }

    const search = document.getElementById('filter-student-search')?.value || '';
    const college = document.getElementById('filter-student-college')?.value || '';
    const skill = document.getElementById('filter-student-skill')?.value || '';
    const role = document.getElementById('filter-student-role')?.value || '';
    const avail = document.getElementById('filter-student-avail')?.value || '';
    const exp = document.getElementById('filter-student-exp')?.value || '';
    const gapTeamId = document.getElementById('filter-student-gap-team')?.value || '';

    const params = new URLSearchParams({
        page: page,
        per_page: 18
    });
    if (search) params.append('skill', search);
    if (college) params.append('college', college);
    if (skill) params.append('skill', skill);
    if (role) params.append('role', role);
    if (avail) params.append('availability', avail);
    if (exp) params.append('experience', exp);
    if (gapTeamId) params.append('fills_gap_for_team_id', gapTeamId);

    try {
        const res = await fetch(`${API_BASE}/students?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) throw new Error('Failed to load students');
        const data = await res.json();
        state.browseStudents = data;
        renderBrowseStudentsList(data);
        renderPagination('students-pagination', data.page, data.pages, loadBrowseStudents);
    } catch (err) {
        container.innerHTML = `<div class="col-span-3 text-center py-8 text-rose-400 text-xs">${err.message}</div>`;
    }
}

function renderBrowseStudentsList(data) {
    const container = document.getElementById('students-browse-grid');
    if (!container) return;
    if (data.items.length === 0) {
        container.innerHTML = `<div class="col-span-3 text-center py-12 text-slate-400 text-xs">No students match your filter criteria.</div>`;
        return;
    }

    container.innerHTML = data.items.map(student => {
        const prof = student.skill_proficiency || {};
        const skillsChips = (student.skills || []).slice(0, 5).map(s => {
            const lvl = prof[s] || 3;
            return `<span class="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">${s} <span class="text-amber-400 font-bold ml-0.5">★${lvl}</span></span>`;
        }).join('');

        const rolesChips = (student.preferred_roles || []).slice(0, 2).map(r => `
            <span class="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-950/70 text-purple-300 border border-purple-800/60">${r}</span>
        `).join('');

        return `
            <div class="glass-card rounded-2xl p-5 border-slate-800 hover:border-purple-600/60 transition flex flex-col justify-between space-y-4">
                <div class="space-y-3">
                    <div class="flex items-start justify-between gap-3">
                        <div class="flex items-center gap-3">
                            <div class="relative">
                                <img src="${student.avatar_url || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + student.id}" class="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700">
                                ${student.is_verified ? '<span class="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 text-slate-950 rounded-full flex items-center justify-center text-[10px] font-bold"><i class="fa-solid fa-check"></i></span>' : ''}
                            </div>
                            <div>
                                <div class="flex items-center gap-1.5">
                                    <h3 class="text-sm font-bold text-white">${student.name}</h3>
                                    ${student.student_id ? '<span class="text-[10px] text-slate-500 font-mono">' + student.student_id + '</span>' : ''}
                                </div>
                                <p class="text-xs text-indigo-300/80 truncate max-w-[180px]"><i class="fa-solid fa-graduation-cap text-[10px] mr-1"></i>${student.college}</p>
                                <p class="text-[11px] text-slate-500">${student.experience_level} • ${student.availability}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="text-xs font-bold text-emerald-400">${Math.round(student.reliability_score || 75)}</span>
                            <span class="text-[9px] text-slate-500 block -mt-1">Reliability</span>
                        </div>
                    </div>

                    ${student.bio ? `<p class="text-xs text-slate-300 line-clamp-2 italic">"${student.bio}"</p>` : ''}

                    <div class="space-y-1.5">
                        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Skills & Proficiency (1-5):</p>
                        <div class="flex flex-wrap gap-1">
                            ${skillsChips || '<span class="text-[10px] text-slate-500">None specified</span>'}
                        </div>
                    </div>

                    ${rolesChips ? `
                    <div class="space-y-1">
                        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Preferred Roles:</p>
                        <div class="flex flex-wrap gap-1">${rolesChips}</div>
                    </div>` : ''}

                    ${student.collaboration_preference ? `
                    <div class="p-2 rounded-lg bg-slate-900/60 border border-slate-800/80 text-[11px] text-slate-400 line-clamp-1">
                        <i class="fa-solid fa-handshake text-indigo-400 mr-1"></i>${student.collaboration_preference}
                    </div>` : ''}
                </div>

                <div class="flex items-center justify-between pt-3 border-t border-slate-800 gap-2">
                    <button onclick="openPublicProfileModal(${student.id})" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition font-medium">
                        Inspect
                    </button>
                    <button onclick="openInviteModal(${student.id}, '${student.name.replace(/'/g, "\\'")}', null, '')" class="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-md transition flex items-center gap-1">
                        <i class="fa-solid fa-paper-plane text-[10px]"></i> Invite
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function renderPagination(elementId, currentPage, totalPages, onPageChange) {
    const container = document.getElementById(elementId);
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = '';
        return;
    }

    container.innerHTML = `
        <button onclick="${onPageChange.name}(${Math.max(1, currentPage - 1)})" ${currentPage === 1 ? 'disabled class="opacity-40 cursor-not-allowed px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300"' : 'class="hover:bg-slate-800 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 transition"'} >
            <i class="fa-solid fa-chevron-left text-xs mr-1"></i> Prev
        </button>
        <span class="text-xs text-slate-400 px-3">Page ${currentPage} of ${totalPages}</span>
        <button onclick="${onPageChange.name}(${Math.min(totalPages, currentPage + 1)})" ${currentPage === totalPages ? 'disabled class="opacity-40 cursor-not-allowed px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300"' : 'class="hover:bg-slate-800 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 transition"'} >
            Next <i class="fa-solid fa-chevron-right text-xs ml-1"></i>
        </button>
    `;
}

// --- TEAM JOIN REQUESTS MANAGEMENT ---
async function loadTeamJoinRequests(teamId) {
    const card = document.getElementById('team-join-requests-card');
    const list = document.getElementById('team-join-requests-list');
    const countBadge = document.getElementById('team-join-requests-count');
    if (!card || !list || !state.token) return;

    try {
        const res = await fetch(`${API_BASE}/teams/${teamId}/join-requests`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (!res.ok) {
            card.classList.add('hidden');
            return;
        }
        const requests = await res.json();
        const pending = requests.filter(r => r.status === 'pending');
        if (countBadge) countBadge.innerText = pending.length;

        if (pending.length === 0) {
            card.classList.add('hidden');
            return;
        }

        card.classList.remove('hidden');
        list.innerHTML = pending.map(r => `
            <div class="p-3 rounded-xl bg-slate-900/80 border border-indigo-900/40 space-y-2">
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2 overflow-hidden">
                        <img src="${r.student_avatar || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + r.user_id}" class="w-7 h-7 rounded-lg bg-slate-800 flex-shrink-0">
                        <div class="truncate">
                            <span class="text-xs font-bold text-white">${r.student_name}</span>
                            <span class="text-[10px] text-slate-400 block">${r.student_id || ''}</span>
                        </div>
                    </div>
                </div>
                <p class="text-[11px] text-slate-300 italic">"${r.message}"</p>
                <div class="flex items-center justify-end gap-1.5 pt-1">
                    <button onclick="handleJoinRequestDecision(${r.id}, 'declined', ${teamId})" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-[11px] font-semibold transition">
                        Decline
                    </button>
                    <button onclick="handleJoinRequestDecision(${r.id}, 'accepted', ${teamId})" class="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold shadow-md transition">
                        Accept & Add
                    </button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error loading join requests:', err);
    }
}

async function handleJoinRequestDecision(requestId, decision, teamId) {
    try {
        const res = await fetch(`${API_BASE}/join-requests/${requestId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ status: decision })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to update request');
        showToast(decision === 'accepted' ? 'Teammate accepted! Roster and skills updated.' : 'Request declined.', 'info');
        showTeamDashboardView(teamId);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// --- CREATE TEAM ---
function openCreateTeamModal() {
    if (!state.token) {
        showToast('Please sign in or use Demo Login to create a team.', 'warning');
        openModal('auth-modal');
        return;
    }
    state.createTeamSkillsMap = {};
    state.createTeamRolesSet = new Set();
    state.createTeamInterestsSet = new Set();

    const picker = document.getElementById('create-team-skills-picker');
    if (picker && state.categories) {
        picker.innerHTML = state.categories.skills.map(skill => {
            const safeKey = skill.replace(/[^a-zA-Z0-9]/g, '_');
            return `
                <div class="flex items-center justify-between p-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
                    <label class="flex items-center gap-1.5 cursor-pointer text-slate-300">
                        <input type="checkbox" onchange="toggleCreateTeamSkill('${skill}', this.checked)" class="rounded text-indigo-600 bg-slate-900 border-slate-700">
                        <span>${skill}</span>
                    </label>
                    <div id="create-team-lvl-wrap-${safeKey}" class="hidden flex items-center gap-2">
                        <span class="text-[10px] text-amber-400 font-bold" id="create-team-lvl-lbl-${safeKey}">Min Level 3</span>
                        <input type="range" min="1" max="5" value="3" oninput="setCreateTeamSkillLevel('${skill}', this.value)" class="w-16 h-1 bg-slate-800 rounded accent-indigo-500">
                    </div>
                </div>
            `;
        }).join('');
    }

    const rolesPicker = document.getElementById('create-team-roles-picker');
    if (rolesPicker && state.categories) {
        rolesPicker.innerHTML = state.categories.preferred_roles.map(r => `
            <button type="button" onclick="toggleCreateTeamRole('${r}', this)" class="px-2 py-0.5 rounded text-[11px] font-medium border border-slate-800 text-slate-400 hover:border-slate-700">
                ${r}
            </button>
        `).join('');
    }

    const intPicker = document.getElementById('create-team-interests-picker');
    if (intPicker && state.categories) {
        intPicker.innerHTML = state.categories.interests.map(i => `
            <button type="button" onclick="toggleCreateTeamInterest('${i}', this)" class="px-2 py-0.5 rounded text-[11px] font-medium border border-slate-800 text-slate-400 hover:border-slate-700">
                ${i}
            </button>
        `).join('');
    }

    if (state.user && state.user.college) {
        const cCol = document.getElementById('create-team-college');
        if (cCol) cCol.value = state.user.college;
    }

    openModal('create-team-modal');
}

function toggleCreateTeamSkill(skill, isChecked) {
    const safeKey = skill.replace(/[^a-zA-Z0-9]/g, '_');
    const wrap = document.getElementById(`create-team-lvl-wrap-${safeKey}`);
    if (isChecked) {
        state.createTeamSkillsMap[skill] = 3;
        if (wrap) wrap.classList.remove('hidden');
    } else {
        delete state.createTeamSkillsMap[skill];
        if (wrap) wrap.classList.add('hidden');
    }
}

function setCreateTeamSkillLevel(skill, val) {
    const level = parseInt(val) || 1;
    state.createTeamSkillsMap[skill] = level;
    const safeKey = skill.replace(/[^a-zA-Z0-9]/g, '_');
    const lbl = document.getElementById(`create-team-lvl-lbl-${safeKey}`);
    if (lbl) lbl.innerText = `Min Level ${level}`;
}

function toggleCreateTeamRole(role, btn) {
    if (state.createTeamRolesSet.has(role)) {
        state.createTeamRolesSet.delete(role);
        btn.className = 'px-2 py-0.5 rounded text-[11px] font-medium border border-slate-800 text-slate-400 hover:border-slate-700';
    } else {
        state.createTeamRolesSet.add(role);
        btn.className = 'px-2 py-0.5 rounded text-[11px] font-medium border bg-purple-950 text-purple-200 border-purple-600';
    }
}

function toggleCreateTeamInterest(interest, btn) {
    if (state.createTeamInterestsSet.has(interest)) {
        state.createTeamInterestsSet.delete(interest);
        btn.className = 'px-2 py-0.5 rounded text-[11px] font-medium border border-slate-800 text-slate-400 hover:border-slate-700';
    } else {
        state.createTeamInterestsSet.add(interest);
        btn.className = 'px-2 py-0.5 rounded text-[11px] font-medium border bg-amber-950 text-amber-200 border-amber-600';
    }
}

async function handleCreateTeamSubmit(e) {
    e.preventDefault();
    const teamName = document.getElementById('create-team-name').value;
    const college = document.getElementById('create-team-college').value;
    const desc = document.getElementById('create-team-desc').value;
    const vacancies = parseInt(document.getElementById('create-team-vacancies').value || '3');
    const exp = document.getElementById('create-team-exp').value;
    const avail = document.getElementById('create-team-avail').value;
    const collab = document.getElementById('create-team-collab').value;

    const requiredSkills = Object.keys(state.createTeamSkillsMap);
    const skillReqs = { ...state.createTeamSkillsMap };
    const preferredRoles = Array.from(state.createTeamRolesSet);
    const interests = Array.from(state.createTeamInterestsSet);

    if (requiredSkills.length === 0) {
        showToast('Please select at least one required skill for your team.', 'warning');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/teams`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                team_name: teamName,
                college: college,
                team_description: desc,
                vacancies: vacancies,
                preferred_experience: exp,
                availability: avail,
                collaboration_preference: collab,
                required_skills: requiredSkills,
                skill_requirements: skillReqs,
                preferred_roles: preferredRoles,
                interests: interests
            })
        });
        const newTeam = await res.json();
        if (!res.ok) throw new Error(newTeam.detail || 'Failed to create team');

        closeModal('create-team-modal');
        showToast(`Team '${newTeam.name}' created successfully!`, 'success');
        navigateToTeam(newTeam.id);
    } catch (err) {
        showToast(err.message, 'error');
    }
}
