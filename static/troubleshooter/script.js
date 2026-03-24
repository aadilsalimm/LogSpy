// ── Init ─────────────────────────────────────────────────────────
lucide.createIcons();

// ── Page entrance animation (slide in from right) ────────────────
document.body.classList.add('swipe-in-from-right');

// ── Nav back button (back to Log-Spy) ────────────────────────────
document.getElementById('nav-back-btn').addEventListener('click', () => {
    document.body.classList.remove('swipe-in-from-right');
    document.body.classList.add('swipe-out-to-right');
    setTimeout(() => {
        window.location.href = '/?from=troubleshooter';
    }, 380);
});

// ── State ─────────────────────────────────────────────────────────
const state = {
    isConnected: false,
    currentResult: null,
    currentProblem: '',
    currentTimeframe: '1h',
    sessions: [],          // { problem, timeframe, result }
    isAnalyzing: false
};

// ── DOM refs ──────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const pages = {
    chat: $('page-chat'),
    loading: $('page-loading'),
    result: $('page-result')
};

// ── Page navigation ───────────────────────────────────────────────
function showPage(name) {
    Object.values(pages).forEach(p => {
        p.classList.remove('active', 'fade-in');
    });
    const target = pages[name];
    target.classList.add('active', 'fade-in');
    lucide.createIcons();
}

// ── SocketIO setup ────────────────────────────────────────────────
const socket = io('http://localhost:5000');

socket.on('connect', () => {
    state.isConnected = true;
    updateConnectionBadge();
});

socket.on('disconnect', () => {
    state.isConnected = false;
    updateConnectionBadge();
});

// Main result event — backend sends completed analysis
socket.on('troubleshoot_result', (data) => {
    clearLoadingInterval();
    state.currentResult = data;

    // Store session
    const session = {
        problem: state.currentProblem,
        timeframe: state.currentTimeframe,
        result: data,
        time: new Date().toLocaleTimeString()
    };
    state.sessions.push(session);

    // Add row to history table
    addHistoryRow(session, state.sessions.length - 1);

    renderResult(data, state.currentProblem, state.currentTimeframe);
    showPage('result');
    state.isAnalyzing = false;
    $('send-btn').disabled = false;
});

// Step progress events (optional — backend can emit these)
socket.on('troubleshoot_step', (data) => {
    // data: { step: 1|2|3 }
    advanceLoadingStep(data.step);
});

// Error event from backend
socket.on('troubleshoot_error', (data) => {
    clearLoadingInterval();
    state.isAnalyzing = false;
    $('send-btn').disabled = false;
    showPage('chat');
    showError(data.message || 'An unexpected error occurred.');
});

// ── Connection badge ──────────────────────────────────────────────
function updateConnectionBadge() {
    const badge = $('connection-badge');
    const iconWrap = $('wifi-icon-wrapper');
    const text = $('connection-text');

    if (state.isConnected) {
        badge.classList.remove('offline');
        badge.classList.add('online');
        iconWrap.innerHTML = '<i data-lucide="wifi" size="14"></i>';
        text.textContent = 'LIVE';
    } else {
        badge.classList.remove('online');
        badge.classList.add('offline');
        iconWrap.innerHTML = '<i data-lucide="wifi-off" size="14"></i>';
        text.textContent = 'OFFLINE';
    }
    lucide.createIcons();
}

// ── Error banner ──────────────────────────────────────────────────
function showError(msg) {
    $('error-message').textContent = msg;
    $('error-banner').classList.remove('hidden');
}
function hideError() {
    $('error-banner').classList.add('hidden');
}
$('error-dismiss').addEventListener('click', hideError);

// ── History table ──────────────────────────────────────────────────
function addHistoryRow(session, idx) {
    const empty = $('history-empty');
    if (empty) empty.classList.add('hidden');

    const tbody = $('history-body');
    const tr = document.createElement('tr');
    tr.addEventListener('click', () => viewSession(idx));
    tr.innerHTML = `
        <td>${idx + 1}</td>
        <td title="${escapeHtml(session.problem)}">${escapeHtml(session.problem)}</td>
        <td>${session.timeframe}</td>
        <td>${session.time}</td>
    `;
    tbody.appendChild(tr);
}

function viewSession(idx) {
    const session = state.sessions[idx];
    if (!session) return;
    state.currentResult = session.result;
    state.currentProblem = session.problem;
    state.currentTimeframe = session.timeframe;
    renderResult(session.result, session.problem, session.timeframe);
    showPage('result');
}

// ── Loading steps ─────────────────────────────────────────────────
let loadingInterval = null;
let loadingStepIndex = 0;

const stepMessages = [
    ['Analyzing your problem...', 'Identifying system components'],
    ['Fetching system logs...', 'Querying journalctl'],
    ['Diagnosing root cause...', 'Running log analysis']
];

function startLoadingAnimation() {
    loadingStepIndex = 1;

    // Reset steps
    for (let i = 1; i <= 3; i++) {
        const s = $(`step-${i}-status`);
        s.className = 'step-status waiting';
        s.textContent = '—';
    }

    advanceLoadingStep(1);

    // Auto-advance steps if backend doesn't emit step events
    // loadingInterval = setInterval(() => {
    //     if (loadingStepIndex < 3) {
    //         loadingStepIndex++;
    //         advanceLoadingStep(loadingStepIndex);
    //     }
    // }, 4000);
}

function advanceLoadingStep(step) {
    // Mark previous steps done
    for (let i = 1; i < step; i++) {
        const s = $(`step-${i}-status`);
        s.className = 'step-status done';
        s.innerHTML = '<i data-lucide="check" size="12"></i>';
    }
    // Mark current step pending
    const cur = $(`step-${step}-status`);
    cur.className = 'step-status pending';
    cur.innerHTML = '<i data-lucide="loader" size="12"></i>';

    if (stepMessages[step - 1]) {
        $('loading-title').textContent = stepMessages[step - 1][0];
        $('loading-sub').textContent = stepMessages[step - 1][1];
    }
    lucide.createIcons();
}

function clearLoadingInterval() {
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }
}

// ── Send logic ────────────────────────────────────────────────────
function sendProblem() {
    const input = $('problem-input');
    const problem = input.value.trim();
    const timeframe = $('timeframe-select').value;

    if (!problem || state.isAnalyzing) return;
    if (!state.isConnected) {
        showError('Not connected to backend. Please make sure the server is running.');
        return;
    }

    hideError();
    state.currentProblem = problem;
    state.currentTimeframe = timeframe;
    state.isAnalyzing = true;

    input.value = '';
    autoResizeTextarea(input);

    $('send-btn').disabled = true;

    // Show loading page
    startLoadingAnimation();
    showPage('loading');

    // Emit to backend
    socket.emit('troubleshoot', {
        problem: problem,
        timeframe: timeframe
    });
}

$('send-btn').addEventListener('click', sendProblem);

$('problem-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendProblem();
    }
});

$('problem-input').addEventListener('input', function () {
    autoResizeTextarea(this);
});

function autoResizeTextarea(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ── Back button ───────────────────────────────────────────────────
$('back-btn').addEventListener('click', () => {
    showPage('chat');
});

// ── Render result ─────────────────────────────────────────────────
function renderResult(data, problem, timeframe) {
    // Header
    $('result-problem-label').textContent = problem;
    $('result-timeframe-badge').textContent = '⏱ last ' + timeframe;

    // Expert banner
    if (data.requires_expert) {
        $('expert-banner').classList.remove('hidden');
    } else {
        $('expert-banner').classList.add('hidden');
    }

    // Root cause
    $('rc-summary').textContent = data.root_cause.summary;
    renderConfidence(data.root_cause.confidence);

    // Evidence
    const evidenceList = $('evidence-list');
    evidenceList.innerHTML = '';
    if (data.root_cause.evidence && data.root_cause.evidence.length > 0) {
        data.root_cause.evidence.forEach(e => {
            const el = document.createElement('div');
            el.className = 'evidence-item';
            el.innerHTML = `
                <div class="evidence-component">${escapeHtml(e.component)}</div>
                <div class="evidence-logline">${escapeHtml(e.log_line)}</div>
                <div class="evidence-interpretation">${escapeHtml(e.interpretation)}</div>
            `;
            evidenceList.appendChild(el);
        });
    } else {
        evidenceList.innerHTML = '<p style="color:var(--muted);font-size:0.82rem">No specific log lines identified.</p>';
    }

    // Contributing factors
    const factorsSection = $('factors-section');
    const factorsList = $('factors-list');
    factorsList.innerHTML = '';
    if (data.contributing_factors && data.contributing_factors.length > 0) {
        factorsSection.classList.remove('hidden');
        data.contributing_factors.forEach(f => {
            const el = document.createElement('div');
            el.className = 'factor-item';
            el.innerHTML = `
                <div class="factor-dot"></div>
                <div>
                    <div class="factor-name">${escapeHtml(f.factor)}</div>
                    <div class="factor-evidence">${escapeHtml(f.evidence)}</div>
                </div>
            `;
            factorsList.appendChild(el);
        });
    } else {
        factorsSection.classList.add('hidden');
    }

    // Suggestions
    const suggList = $('suggestions-list');
    suggList.innerHTML = '';
    if (data.suggestions && data.suggestions.length > 0) {
        data.suggestions.forEach((s, i) => {
            const el = document.createElement('div');
            el.className = 'suggestion-item';

            const cmdHtml = s.command ? `
                <div class="command-row">
                    <span class="dollar">$</span>
                    <span class="cmd-text" id="cmd-${i}">${escapeHtml(s.command)}</span>
                    <button class="copy-btn" onclick="copyCmd('cmd-${i}', this)">copy</button>
                </div>` : '';

            el.innerHTML = `
                <div class="step-num">${i + 1}</div>
                <div>
                    <div class="suggestion-action">${escapeHtml(s.action)}</div>
                    <div class="suggestion-explanation">${escapeHtml(s.explanation)}</div>
                    ${cmdHtml}
                </div>
            `;
            suggList.appendChild(el);
        });
    }

    // Log coverage note
    const coverageSection = $('coverage-section');
    if (data.log_coverage_note) {
        coverageSection.classList.remove('hidden');
        $('coverage-note').textContent = data.log_coverage_note;
    } else {
        coverageSection.classList.add('hidden');
    }

    lucide.createIcons();
}

// ── Confidence bar ────────────────────────────────────────────────
function renderConfidence(level) {
    const pips = [$('pip-1'), $('pip-2'), $('pip-3')];
    const counts = { high: 3, medium: 2, low: 1 };
    const filled = counts[level] || 1;

    pips.forEach((pip, i) => {
        pip.className = 'conf-pip';
        if (i < filled) pip.classList.add('filled', level);
    });

    const text = $('conf-text');
    text.textContent = level;
    text.className = 'conf-text ' + level;
}

// ── Copy command ──────────────────────────────────────────────────
function copyCmd(id, btn) {
    const text = $(id).textContent;
    navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'copied';
        setTimeout(() => btn.textContent = 'copy', 1500);
    });
}

// ── Utility ───────────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
