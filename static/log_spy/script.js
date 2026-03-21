// Initialize Lucide icons
lucide.createIcons();

// --- STATE MANAGEMENT ---
const state = {
    isConnected: false,
    data: null,
    history: [],
    isModalOpen: false,
    error: null,
    fullHistory: [],
    fullHistorySort: 'desc',
    fullHistoryFilter: 'all',
    selectedIds: new Set()
};

// --- DOM ELEMENTS ---
const elements = {
    connectionBadge: document.getElementById('connection-badge'),
    wifiIconWrapper: document.getElementById('wifi-icon-wrapper'),
    connectionText: document.getElementById('connection-text'),
    lastUpdate: document.getElementById('last-update'),
    errorBanner: document.getElementById('error-banner'),
    errorMessage: document.getElementById('error-message'),

    statusCard: document.getElementById('status-card'),
    statusIconWrapper: document.getElementById('status-icon-wrapper'),
    statusTitle: document.getElementById('status-title'),
    statusDescription: document.getElementById('status-description'),

    historyBody: document.getElementById('history-body'),

    modalOverlay: document.getElementById('modal-overlay'),
    modalReason: document.getElementById('modal-reason'),
    modalTimestamp: document.getElementById('modal-timestamp'),
    modalCloseBtn: document.getElementById('modal-close-btn'),
    modalAckBtn: document.getElementById('modal-acknowledge-btn'),

    showFullHistoryBtn: document.getElementById('show-full-history-btn'),
    fullHistoryOverlay: document.getElementById('full-history-overlay'),
    fullHistoryCloseBtn: document.getElementById('full-history-close-btn'),
    fullHistoryBody: document.getElementById('full-history-body'),
    fullHistorySortBtn: document.getElementById('full-history-sort-btn'),
    sortLabel: document.getElementById('sort-label'),
    fullHistoryFilter: document.getElementById('full-history-filter'),
    fullHistoryDeleteBtn: document.getElementById('full-history-delete-btn'),
    fullHistoryClearBtn: document.getElementById('full-history-clear-btn'),
    fullHistorySelectAll: document.getElementById('full-history-select-all'),
    troubleshooterBtn: document.getElementById('troubleshooter-btn')
};

// --- UI UPDATE FUNCTIONS ---

function updateHeader() {
    if (state.isConnected) {
        elements.connectionBadge.classList.remove('offline');
        elements.connectionBadge.classList.add('online');
        elements.connectionText.textContent = 'LIVE';

        elements.wifiIconWrapper.innerHTML = '<i data-lucide="wifi" size="14"></i>';
    } else {
        elements.connectionBadge.classList.remove('online');
        elements.connectionBadge.classList.add('offline');
        elements.connectionText.textContent = 'OFFLINE';

        elements.wifiIconWrapper.innerHTML = '<i data-lucide="wifi-off" size="14"></i>';
    }

    if (state.data?.timestamp) {
        elements.lastUpdate.textContent = new Date(state.data.timestamp).toLocaleTimeString();
    }

    lucide.createIcons(); // Refresh icons
}

function updateStatusCard() {
    const isAnomalous = state.data?.is_anomalous;

    if (isAnomalous) {
        elements.statusCard.classList.add('anomaly');
        elements.statusIconWrapper.innerHTML = '<i data-lucide="shield-alert" size="64" stroke-width="1.5"></i>';
        elements.statusTitle.textContent = "Anomaly Detected";
        elements.statusDescription.textContent = "Critical system event requires attention.";
    } else {
        elements.statusCard.classList.remove('anomaly');
        elements.statusIconWrapper.innerHTML = '<i data-lucide="shield-check" size="64" stroke-width="1.5"></i>';
        elements.statusTitle.textContent = "System Normal";
        elements.statusDescription.textContent = "No irregularities detected in system logs.";
    }
    lucide.createIcons();
}

function updateHistory() {
    if (state.history.length === 0) {
        elements.historyBody.innerHTML = `
            <tr>
                <td colspan="3" class="history-empty">No anomalies recorded yet.</td>
            </tr>
        `;
        return;
    }

    elements.historyBody.innerHTML = state.history.map(entry => `
        <tr>
            <td class="history-td history-timestamp">
                ${entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : 'N/A'}
            </td>
            <td class="history-td">
                ${entry.component || 'N/A'}
            </td>
            <td class="history-td history-reason">
                ${entry.reason}
            </td>
        </tr>
    `).join('');

    lucide.createIcons();
}

function toggleModal(open) {
    state.isModalOpen = open;
    if (open && state.data) {
        elements.modalReason.textContent = state.data.reason || "Unknown";
        elements.modalTimestamp.textContent = new Date(state.data.timestamp).toLocaleTimeString();
        elements.modalOverlay.classList.add('open');
    } else {
        elements.modalOverlay.classList.remove('open');
    }
}

// --- FULL HISTORY PANEL ---

function toggleFullHistory(open) {
    if (open) {
        elements.fullHistoryOverlay.classList.add('open');
    } else {
        elements.fullHistoryOverlay.classList.remove('open');
    }
}

function getFilteredSortedHistory() {
    let data = [...state.fullHistory];

    // Filter
    if (state.fullHistoryFilter === 'anomalous') {
        data = data.filter(e => e.is_anomalous === 1 || e.is_anomalous === true);
    } else if (state.fullHistoryFilter === 'normal') {
        data = data.filter(e => e.is_anomalous === 0 || e.is_anomalous === false);
    }

    // Sort by timestamp
    data.sort((a, b) => {
        const tA = new Date(a.timestamp).getTime();
        const tB = new Date(b.timestamp).getTime();
        return state.fullHistorySort === 'desc' ? tB - tA : tA - tB;
    });

    return data;
}

function renderFullHistory() {
    const data = getFilteredSortedHistory();

    if (data.length === 0) {
        elements.fullHistoryBody.innerHTML = `
            <tr>
                <td colspan="5" class="history-empty">No logs match the current filter.</td>
            </tr>
        `;
        updateDeleteBtnState();
        lucide.createIcons();
        return;
    }

    elements.fullHistoryBody.innerHTML = data.map(entry => {
        const id = entry.id ?? entry.timestamp;
        const isChecked = state.selectedIds.has(id) ? 'checked' : '';
        const isAnomaly = entry.is_anomalous === 1 || entry.is_anomalous === true;
        const statusClass = isAnomaly ? 'anomalous' : 'normal';
        const statusText = isAnomaly ? 'Anomaly' : 'Normal';
        const selectedClass = state.selectedIds.has(id) ? 'selected' : '';

        return `
        <tr class="${selectedClass}" data-id="${id}">
            <td class="history-td td-checkbox">
                <input type="checkbox" class="row-checkbox full-history-row-cb" data-id="${id}" ${isChecked} />
            </td>
            <td class="history-td history-timestamp">
                ${entry.timestamp ? new Date(entry.timestamp).toLocaleString() : 'N/A'}
            </td>
            <td class="history-td">
                <span class="status-badge ${statusClass}">${statusText}</span>
            </td>
            <td class="history-td">
                ${entry.component || 'N/A'}
            </td>
            <td class="history-td history-reason">
                ${entry.reason || 'N/A'}
            </td>
        </tr>`;
    }).join('');

    updateDeleteBtnState();
    updateSelectAllState();
    lucide.createIcons();
}

function updateDeleteBtnState() {
    elements.fullHistoryDeleteBtn.disabled = state.selectedIds.size === 0;
}

function updateSelectAllState() {
    const visible = getFilteredSortedHistory();
    const allChecked = visible.length > 0 && visible.every(e => state.selectedIds.has(e.id ?? e.timestamp));
    elements.fullHistorySelectAll.checked = allChecked;
}

// --- DATA LOGIC ---

//  * processData handles the logic when new data arrives (real or simulated).
function processData(newData) {
    state.data = newData;
    state.isConnected = true;

    // Check for anomaly
    if (newData.is_anomalous) {
        // Add to history if it's a new anomaly or different timestamp
        const lastEntry = state.history[0];
        if (!lastEntry || lastEntry.timestamp !== newData.timestamp) {
            state.history.unshift(newData); // Add to top
            toggleModal(true);
        }
    }

    updateHeader();
    updateStatusCard();
    updateHistory();
}


let socket;

function startConnection() {
    socket = io('http://localhost:5000');

    socket.on("connect", () => {
        state.isConnected = true;
        console.log("socket connected.")
        updateHeader();
    });

    socket.on("anomaly_update", (data) => {
        console.log("recived data: " + data)
        processData(data);
    });

    // Receive full history from backend
    socket.on("full_history", (data) => {
        console.log("Received full history:", data);
        state.fullHistory = Array.isArray(data) ? data : [];
        state.selectedIds.clear();
        renderFullHistory();
        toggleFullHistory(true);
    });

    socket.on("disconnect", () => {
        state.isConnected = false;
        updateHeader();
    });
}
startConnection();



// --- EVENT LISTENERS ---

elements.modalCloseBtn.addEventListener('click', () => toggleModal(false));
elements.modalAckBtn.addEventListener('click', () => toggleModal(false));

// Open Troubleshooter App
elements.troubleshooterBtn.addEventListener('click', () => {
    if (socket && socket.connected) {
        socket.emit('open_troubleshooter');
        console.log('Troubleshooter event emitted.');
    } else {
        console.warn('Socket not connected. Cannot open troubleshooter.');
    }
});

// Close modal on click outside
elements.modalOverlay.addEventListener('click', (e) => {
    if (e.target === elements.modalOverlay) {
        toggleModal(false);
    }
});

// --- FULL HISTORY EVENT LISTENERS ---

// Open full history panel — request data from backend
elements.showFullHistoryBtn.addEventListener('click', () => {
    elements.fullHistoryBody.innerHTML = `
        <tr><td colspan="5" class="history-empty">Loading...</td></tr>
    `;
    toggleFullHistory(true);
    if (socket && socket.connected) {
        socket.emit('get_full_history');
    }
});

// Close full history panel
elements.fullHistoryCloseBtn.addEventListener('click', () => toggleFullHistory(false));
elements.fullHistoryOverlay.addEventListener('click', (e) => {
    if (e.target === elements.fullHistoryOverlay) {
        toggleFullHistory(false);
    }
});

// Sort toggle
elements.fullHistorySortBtn.addEventListener('click', () => {
    state.fullHistorySort = state.fullHistorySort === 'desc' ? 'asc' : 'desc';
    elements.sortLabel.textContent = state.fullHistorySort === 'desc' ? 'Newest First' : 'Oldest First';
    renderFullHistory();
});

// Filter
elements.fullHistoryFilter.addEventListener('change', (e) => {
    state.fullHistoryFilter = e.target.value;
    state.selectedIds.clear();
    renderFullHistory();
});

// Row checkbox delegation
elements.fullHistoryBody.addEventListener('change', (e) => {
    if (e.target.classList.contains('full-history-row-cb')) {
        const id = e.target.dataset.id;
        if (e.target.checked) {
            state.selectedIds.add(isNaN(id) ? id : Number(id));
        } else {
            state.selectedIds.delete(isNaN(id) ? id : Number(id));
        }
        // Update row styling
        const row = e.target.closest('tr');
        row.classList.toggle('selected', e.target.checked);
        updateDeleteBtnState();
        updateSelectAllState();
    }
});

// Select all checkbox
elements.fullHistorySelectAll.addEventListener('change', (e) => {
    const visible = getFilteredSortedHistory();
    if (e.target.checked) {
        visible.forEach(entry => state.selectedIds.add(entry.id ?? entry.timestamp));
    } else {
        visible.forEach(entry => state.selectedIds.delete(entry.id ?? entry.timestamp));
    }
    renderFullHistory();
});

// Delete selected
elements.fullHistoryDeleteBtn.addEventListener('click', () => {
    if (state.selectedIds.size === 0) return;
    const idsToDelete = [...state.selectedIds];
    if (socket && socket.connected) {
        socket.emit('delete_logs', idsToDelete);
    }
    // Optimistically remove from local state
    state.fullHistory = state.fullHistory.filter(e => !state.selectedIds.has(e.id ?? e.timestamp));
    state.selectedIds.clear();
    renderFullHistory();
});

// Clear all
elements.fullHistoryClearBtn.addEventListener('click', () => {
    if (!confirm('Are you sure you want to clear all history? This cannot be undone.')) return;
    if (socket && socket.connected) {
        socket.emit('clear_history');
    }
    // Optimistically clear local state
    state.fullHistory = [];
    state.selectedIds.clear();
    renderFullHistory();
});
