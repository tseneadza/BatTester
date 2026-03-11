let activeTestId = null;
let chart = null;
let pollInterval = null;

const API = {
    async get(path) {
        const res = await fetch(`/api${path}`);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
    async post(path, data = {}) {
        const res = await fetch(`/api${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
};

function initChart() {
    const ctx = document.getElementById('voltage-chart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Voltage (V)',
                data: [],
                borderColor: '#4fc3f7',
                backgroundColor: 'rgba(79, 195, 247, 0.1)',
                fill: true,
                tension: 0.3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Time', color: '#9aa0a6' },
                    ticks: { color: '#9aa0a6', maxTicksLimit: 10 },
                    grid: { color: '#3a4556' },
                },
                y: {
                    display: true,
                    title: { display: true, text: 'Voltage (V)', color: '#9aa0a6' },
                    ticks: { color: '#9aa0a6' },
                    grid: { color: '#3a4556' },
                },
            },
        },
    });
}

function formatDuration(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

async function loadTests() {
    const tests = await API.get('/tests');
    const list = document.getElementById('test-list');
    
    if (tests.length === 0) {
        list.innerHTML = '<p class="empty-state">No tests yet. Create one above.</p>';
        return;
    }
    
    list.innerHTML = tests.map(t => `
        <div class="test-item ${t.id === activeTestId ? 'active' : ''}" data-id="${t.id}">
            <div class="test-info">
                <h3>${t.name}</h3>
                <p>${t.capacity_mah.toFixed(0)} mAh · ${formatDuration(t.duration_seconds)}</p>
            </div>
            <span class="test-status status-${t.state}">${t.state}</span>
        </div>
    `).join('');
    
    list.querySelectorAll('.test-item').forEach(el => {
        el.addEventListener('click', () => selectTest(el.dataset.id));
    });
}

async function selectTest(testId) {
    activeTestId = testId;
    const test = await API.get(`/tests/${testId}`);
    
    document.getElementById('active-test').style.display = 'block';
    document.getElementById('active-test-name').textContent = test.name;
    
    updateMetrics(test);
    updateControls(test.state);
    await loadReadings();
    loadTests();
}

function updateMetrics(test) {
    document.getElementById('metric-voltage').textContent = 
        test.voltage?.toFixed(3) ?? '--';
    document.getElementById('metric-current').textContent = 
        test.current_ma?.toFixed(0) ?? '--';
    document.getElementById('metric-temp').textContent = 
        test.temperature_c?.toFixed(1) ?? '--';
    document.getElementById('metric-capacity').textContent = 
        test.capacity_mah.toFixed(0);
    document.getElementById('metric-energy').textContent = 
        test.energy_mwh.toFixed(0);
    document.getElementById('metric-duration').textContent = 
        formatDuration(test.duration_seconds);
}

function updateControls(state) {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    const isRunning = state === 'discharging' || state === 'charging';
    startBtn.disabled = isRunning;
    stopBtn.disabled = !isRunning;
    
    if (isRunning && !pollInterval) {
        pollInterval = setInterval(pollTest, 1000);
    } else if (!isRunning && pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function loadReadings() {
    if (!activeTestId) return;
    
    const readings = await API.get(`/tests/${activeTestId}/readings?limit=100`);
    
    chart.data.labels = readings.map((_, i) => i);
    chart.data.datasets[0].data = readings.map(r => r.voltage);
    chart.update('none');
}

async function pollTest() {
    if (!activeTestId) return;
    
    try {
        const test = await API.get(`/tests/${activeTestId}`);
        updateMetrics(test);
        updateControls(test.state);
        await loadReadings();
        
        if (test.state === 'complete' || test.state === 'error') {
            loadTests();
        }
    } catch (e) {
        console.error('Poll error:', e);
    }
}

document.getElementById('create-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const test = await API.post('/tests', {
        name: document.getElementById('test-name').value,
        chemistry: document.getElementById('chemistry').value,
        nominal_voltage: parseFloat(document.getElementById('voltage').value),
        capacity_mah: parseInt(document.getElementById('capacity').value),
        cell_count: parseInt(document.getElementById('cells').value),
    });
    
    await loadTests();
    selectTest(test.id);
});

document.getElementById('start-btn').addEventListener('click', async () => {
    if (!activeTestId) return;
    
    const rate = parseFloat(document.getElementById('discharge-rate').value);
    await API.post(`/tests/${activeTestId}/start`, { discharge_rate_c: rate });
    
    const test = await API.get(`/tests/${activeTestId}`);
    updateControls(test.state);
    loadTests();
});

document.getElementById('stop-btn').addEventListener('click', async () => {
    if (!activeTestId) return;
    
    await API.post(`/tests/${activeTestId}/stop`);
    
    const test = await API.get(`/tests/${activeTestId}`);
    updateControls(test.state);
    loadTests();
});

initChart();
loadTests();
