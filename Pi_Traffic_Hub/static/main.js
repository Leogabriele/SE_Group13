const socket = io();

// UI Elements
const statusBadge = document.getElementById('connection-status');
const logsBox = document.getElementById('logs-box');
const sensorCV = document.getElementById('sensor-cv');
const sensorRF = document.getElementById('sensor-rf');
const rfHwStatus = document.getElementById('rf-hw-status');

socket.on('connect', () => {
    statusBadge.textContent = 'SYSTEM SECURED';
    statusBadge.className = 'status-badge connected';
});

socket.on('disconnect', () => {
    statusBadge.textContent = 'CONNECTION LOST';
    statusBadge.className = 'status-badge connecting';
});

socket.on('new_log', (data) => {
    const el = document.createElement('div');
    el.className = 'log-entry';
    el.textContent = data.log;
    if (data.log.includes('VERIFICATION') || data.log.includes('OVERRIDE')) {
        el.classList.add('override');
    }
    logsBox.prepend(el);
});

socket.on('state_update', (data) => {
    // 1. Update CV Sensor
    if (data.cv_detected) {
        sensorCV.classList.add('active');
        sensorCV.querySelector('.status').textContent = 'DETECTED';
    } else {
        sensorCV.classList.remove('active');
        sensorCV.querySelector('.status').textContent = 'AWAITING FRAMES...';
    }

    // 2. Update RF Sensor with live diagnostics
    if (data.rf_detected) {
        sensorRF.classList.add('active');
        sensorRF.querySelector('.status').textContent = 'SIGNAL SECURED';
    } else {
        sensorRF.classList.remove('active');
        sensorRF.querySelector('.status').textContent = 'NO SIGNAL';
    }

    // 2b. RF hardware diagnostic details
    if (rfHwStatus && data.rf_diag) {
        const d = data.rf_diag;
        if (!d.lib_available) {
            rfHwStatus.textContent = 'pyrf24 not installed';
            rfHwStatus.className = 'rf-hw-status offline';
        } else if (!d.hw_online) {
            rfHwStatus.textContent = 'NRF24 OFFLINE — ' + d.info;
            rfHwStatus.className = 'rf-hw-status offline';
        } else {
            rfHwStatus.textContent = d.info;
            rfHwStatus.className = d.esp32_connected ? 'rf-hw-status online' : 'rf-hw-status offline';
        }
    }

    // 3. Update Traffic Lights using per-lane state (supports yellow!)
    document.querySelectorAll('.bulb').forEach(b => b.classList.remove('active'));

    const lanes = [1, 2, 3];
    lanes.forEach(laneNum => {
        const laneDiv = document.getElementById(`lane-${laneNum}`);
        if (!laneDiv) return;

        // Use the actual per-lane light state from the controller
        const state = data.lane_states ? data.lane_states[laneNum] : null;

        if (state) {
            // Activate the correct bulb based on real hardware state
            const bulb = laneDiv.querySelector(`.${state}`);
            if (bulb) bulb.classList.add('active');
        } else {
            // Fallback: if lane_states not available, use old logic
            if (data.emergency_override) {
                if (laneNum === 1) {
                    laneDiv.querySelector('.green').classList.add('active');
                } else {
                    laneDiv.querySelector('.red').classList.add('active');
                }
            } else {
                if (data.current_lane === laneNum) {
                    laneDiv.querySelector('.green').classList.add('active');
                } else {
                    laneDiv.querySelector('.red').classList.add('active');
                }
            }
        }
    });
});
