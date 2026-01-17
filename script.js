// --- 1. Notification & Alerts ---
async function fetchAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const alerts = await response.json();
        
        const countBadge = document.getElementById('notifCount');
        const alertList = document.getElementById('alertList');
        
        if (countBadge && alertList) {
            countBadge.innerText = alerts.length;
            countBadge.style.display = alerts.length > 0 ? 'block' : 'none';
            
            if(alerts.length > 0) {
                alertList.innerHTML = alerts.map(a => `
                    <div style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <strong style="color: ${a.priority === 'High' ? '#ff6b6b' : 'orange'}">${a.type}</strong><br>
                        <span style="font-size: 12px; color: #ccc;">${a.message}</span>
                    </div>
                `).join('');
            } else {
                alertList.innerHTML = '<div style="padding:10px;">No active alerts</div>';
            }
        }
    } catch (e) { console.log("Alert system waiting..."); }
}

function toggleNotifs() {
    const el = document.getElementById('notifDropdown');
    if(el) el.classList.toggle('show');
}

// --- 2. AI Maintenance ---
async function updateAI() {
    try {
        const res = await fetch('/api/predictive_maintenance');
        const data = await res.json();
        
        const predEl = document.getElementById('aiPrediction');
        if(predEl) {
            predEl.innerText = data.prediction;
            predEl.style.color = data.status_color;
            document.getElementById('aiAction').innerText = data.action;
            
            // Update Bars
            document.getElementById('vibBar').style.width = (data.vibration * 100) + '%';
            document.getElementById('tempBar').style.width = data.temperature + '%';
        }
    } catch (e) { console.log("AI system waiting..."); }
}

// --- 3. Workflow ---
async function advanceWorkflow(orderId) {
    // Strip the # if it exists because URL handles it
    const cleanId = orderId.replace('#', '');
    try {
        const res = await fetch(`/api/workflow/next/${cleanId}`, { method: 'POST' });
        const data = await res.json();
        if(data.status === 'success') {
            location.reload(); 
        } else {
            alert("Error: " + data.message);
        }
    } catch (e) { alert("Network Error"); }
}

// --- 4. Auto Order ---
async function triggerAutoOrder() {
    try {
        const res = await fetch('/api/auto_reorder', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
    } catch (e) { alert("Failed to connect to supplier API"); }
}
async function refreshTasks() {
        try {
            // Now calling the real API we just added
            const res = await fetch('/api/orders');
            const orders = await res.json();
            
            const tbody = document.getElementById('operatorTasks');
            if (orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No active tasks</td></tr>';
                return;
            }

            tbody.innerHTML = orders.map(t => `
                <tr>
                    <td>${t.id}</td>
                    <td>${t.product}</td>
                    <td><span class="badge badge-ok">${t.status}</span></td>
                    <td>
                        <button class="primary-btn btn-sm" onclick="advanceWorkflow('${t.id}')">
                            Next Stage <i class="fas fa-chevron-right"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } catch(e) {
            console.log("Error loading tasks");
        }
    }
    // Navbar Scroll Effect
window.addEventListener("scroll", function() {
    var navbar = document.getElementById("navbar");
    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});
// --- 1. Notification & Alerts ---
async function fetchAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const alerts = await response.json();
        
        const countBadge = document.getElementById('notifCount');
        const alertList = document.getElementById('alertList');
        
        if (countBadge && alertList) {
            countBadge.innerText = alerts.length;
            countBadge.style.display = alerts.length > 0 ? 'block' : 'none';
            
            if(alerts.length > 0) {
                alertList.innerHTML = alerts.map(a => `
                    <div style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <strong style="color: ${a.priority === 'High' ? '#ff6b6b' : 'orange'}">${a.type}</strong><br>
                        <span style="font-size: 12px; color: #ccc;">${a.message}</span>
                    </div>
                `).join('');
            } else {
                alertList.innerHTML = '<div style="padding:10px;">No active alerts</div>';
            }
        }
    } catch (e) { console.log("Alert system waiting..."); }
}

function toggleNotifs() {
    const el = document.getElementById('notifDropdown');
    if(el) el.classList.toggle('show');
}
// Update your existing socket.on('ai_ack') or add a new one:
socket.on('ai_ack', (data) => {
    // Check if the command is a material request
    if (data.cmd.includes("REQUEST_MATERIAL")) {
        const alertBox = document.getElementById('managerAlert');
        const content = document.getElementById('alertContent');
        
        content.innerText = data.response || data.cmd; // Showing the manager's request
        alertBox.style.display = 'block';
        
        // Play a notification sound (Optional)
        const audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
        audio.play();
    }
    
    // Existing logic for console log
    document.getElementById('aiLog').innerText = "> " + data.response;
});

function acknowledgeRequest() {
    document.getElementById('managerAlert').style.display = 'none';
    // You can add a fetch call here to update your JSON inventory via an API
    console.log("Material request acknowledged and logged.");
}
// --- 2. AI Maintenance ---
async function updateAI() {
    try {
        const res = await fetch('/api/predictive_maintenance');
        const data = await res.json();
        
        const predEl = document.getElementById('aiPrediction');
        if(predEl) {
            predEl.innerText = data.prediction;
            predEl.style.color = data.status_color;
            document.getElementById('aiAction').innerText = data.action;
            
            // Update Bars
            document.getElementById('vibBar').style.width = (data.vibration * 100) + '%';
            document.getElementById('tempBar').style.width = data.temperature + '%';
        }
    } catch (e) { console.log("AI system waiting..."); }
}

// --- 3. Workflow ---
async function advanceWorkflow(orderId) {
    // Strip the # if it exists because URL handles it
    const cleanId = orderId.replace('#', '');
    try {
        const res = await fetch(`/api/workflow/next/${cleanId}`, { method: 'POST' });
        const data = await res.json();
        if(data.status === 'success') {
            location.reload(); 
        } else {
            alert("Error: " + data.message);
        }
    } catch (e) { alert("Network Error"); }
}

// --- 4. Auto Order ---
async function triggerAutoOrder() {
    try {
        const res = await fetch('/api/auto_reorder', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
    } catch (e) { alert("Failed to connect to supplier API"); }
}
async function refreshTasks() {
        try {
            // Now calling the real API we just added
            const res = await fetch('/api/orders');
            const orders = await res.json();
            
            const tbody = document.getElementById('operatorTasks');
            if (orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No active tasks</td></tr>';
                return;
            }

            tbody.innerHTML = orders.map(t => `
                <tr>
                    <td>${t.id}</td>
                    <td>${t.product}</td>
                    <td><span class="badge badge-ok">${t.status}</span></td>
                    <td>
                        <button class="primary-btn btn-sm" onclick="advanceWorkflow('${t.id}')">
                            Next Stage <i class="fas fa-chevron-right"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } catch(e) {
            console.log("Error loading tasks");
        }
    }
    // Navbar Scroll Effect
window.addEventListener("scroll", function() {
    var navbar = document.getElementById("navbar");
    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});
// Start Polling when page loads
window.onload = function() {
    fetchAlerts();
    updateAI();
    setInterval(fetchAlerts, 5000);
    setInterval(updateAI, 3000);
};
// Start Polling when page loads
window.onload = function() {
    fetchAlerts();
    updateAI();
    setInterval(fetchAlerts, 5000);
    setInterval(updateAI, 3000);
};