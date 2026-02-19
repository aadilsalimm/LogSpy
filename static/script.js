// Initialize Lucide icons
lucide.createIcons();

// --- STATE MANAGEMENT ---
const state = {
    isConnected: false,
    data: null,
    history: [],
    isModalOpen: false,
    error: null
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
    modalAckBtn: document.getElementById('modal-acknowledge-btn')
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
                <span class="history-badge">
                    <i data-lucide="alert-circle" size="12" style="margin-right:4px"></i> Anomaly
                </span>
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

// // --- SIMULATION / DATA LOGIC ---

// /**
//  * processData handles the logic when new data arrives (real or simulated).
//  */
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


function startConnection() {
    const socket = io('http://localhost:5000');
    
    socket.on("connect", () => {
        state.isConnected = true;
        console.log("socket connected.")
        updateHeader();
    });
    
    socket.on("anomaly_update", (data) => {
        console.log("recived data: " + data)
        processData(data);
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

// Close modal on click outside
elements.modalOverlay.addEventListener('click', (e) => {
    if (e.target === elements.modalOverlay) {
        toggleModal(false);
    }
});
