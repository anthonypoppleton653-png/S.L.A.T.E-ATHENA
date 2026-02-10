/* SLATE-ATHENA — Dashboard Logic & WebSocket
 * Modified: 2026-02-10T01:30:00Z | Author: COPILOT | Change: Create main.js with WebSocket, API polling, panel rendering
 *
 * Connects to /ws for real-time updates and polls REST endpoints
 * to populate the control board panels.
 */

(function () {
    'use strict';

    // ─── Config ──────────────────────────────────────────────────────
    const POLL_INTERVAL  = 15000;  // 15s between full polls
    const WS_RETRY_DELAY = 3000;   // 3s before WebSocket reconnect
    const WS_MAX_RETRIES = 20;

    // ─── DOM refs ────────────────────────────────────────────────────
    const $  = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const els = {
        wsDot:      $('.status-dot'),
        wsLabel:    $('.ws-label'),
        headerTime: $('.header-time'),
        gpuBody:    $('#gpuBody'),
        ollamaBody: $('#ollamaBody'),
        servicesBody: $('#servicesBody'),
        tasksBody:  $('#tasksBody'),
        taskCount:  $('#taskCount'),
        resBody:    $('#resourcesBody'),
        runnerBody: $('#runnerBody'),
    };

    // ─── Utility ─────────────────────────────────────────────────────
    function escapeHtml(str) {
        if (!str) return '';
        const d = document.createElement('div');
        d.textContent = String(str);
        return d.innerHTML;
    }

    function formatBytes(bytes) {
        if (!bytes || bytes < 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
    }

    function formatPercent(val) {
        return (val || 0).toFixed(1) + '%';
    }

    // ─── Clock ───────────────────────────────────────────────────────
    function updateClock() {
        if (els.headerTime) {
            els.headerTime.textContent = new Date().toLocaleTimeString('en-US', {
                hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit',
            });
        }
    }
    setInterval(updateClock, 1000);
    updateClock();

    // ─── WebSocket ───────────────────────────────────────────────────
    let ws = null;
    let wsRetries = 0;

    function connectWS() {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${proto}//${location.host}/ws`;

        ws = new WebSocket(url);

        ws.onopen = function () {
            wsRetries = 0;
            setWsStatus(true);
            console.log('[ws] Connected');
        };

        ws.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                handleBroadcast(data);
            } catch (err) {
                console.warn('[ws] Bad message:', err);
            }
        };

        ws.onclose = function () {
            setWsStatus(false);
            scheduleReconnect();
        };

        ws.onerror = function () {
            setWsStatus(false);
            try { ws.close(); } catch (_) {}
        };
    }

    function scheduleReconnect() {
        if (wsRetries < WS_MAX_RETRIES) {
            wsRetries++;
            setTimeout(connectWS, WS_RETRY_DELAY);
        }
    }

    function setWsStatus(connected) {
        if (els.wsDot) {
            els.wsDot.className = 'status-dot ' + (connected ? 'connected' : 'disconnected');
        }
        if (els.wsLabel) {
            els.wsLabel.textContent = connected ? 'Live' : 'Offline';
        }
    }

    function handleBroadcast(data) {
        // The server broadcasts a combined status object
        if (data.gpu)       renderGPU(data.gpu);
        if (data.ollama)    renderOllama(data.ollama);
        if (data.services)  renderServices(data.services);
        if (data.tasks)     renderTasks(data.tasks);
        if (data.resources) renderResources(data.resources);
        if (data.runner)    renderRunner(data.runner);
    }

    // ─── REST Polling ────────────────────────────────────────────────
    async function fetchJSON(url) {
        try {
            const resp = await fetch(url);
            if (!resp.ok) return null;
            return await resp.json();
        } catch (err) {
            return null;
        }
    }

    async function pollAll() {
        const [gpu, ollama, services, tasks, resources, runner] = await Promise.all([
            fetchJSON('/api/gpu'),
            fetchJSON('/api/ollama'),
            fetchJSON('/api/services'),
            fetchJSON('/api/tasks'),
            fetchJSON('/api/system/resources'),
            fetchJSON('/api/runner'),
        ]);

        if (gpu)       renderGPU(gpu);
        if (ollama)    renderOllama(ollama);
        if (services)  renderServices(services);
        if (tasks)     renderTasks(tasks);
        if (resources) renderResources(resources);
        if (runner)    renderRunner(runner);
    }

    // ─── GPU Panel ───────────────────────────────────────────────────
    function renderGPU(data) {
        if (!els.gpuBody) return;
        const gpus = data.gpus || data.devices || [];
        if (gpus.length === 0) {
            els.gpuBody.innerHTML = '<p class="loading-placeholder">No GPUs detected</p>';
            return;
        }
        els.gpuBody.innerHTML = gpus.map((g, i) => {
            const name = escapeHtml(g.name || `GPU ${i}`);
            const memUsed = g.memory_used || g.mem_used || 0;
            const memTotal = g.memory_total || g.mem_total || 1;
            const memPct = ((memUsed / memTotal) * 100).toFixed(0);
            const util = g.utilization || g.gpu_util || 0;
            const temp = g.temperature || g.temp || '?';
            const memClass = memPct > 85 ? 'danger' : memPct > 60 ? 'warn' : '';
            return `
                <div class="gpu-card fade-in">
                    <div class="gpu-name">${name}</div>
                    <div class="gpu-stats">
                        <span>VRAM</span>
                        <span class="stat-value">${formatBytes(memUsed * 1024 * 1024)} / ${formatBytes(memTotal * 1024 * 1024)}</span>
                        <span>Util</span>
                        <span class="stat-value">${util}%</span>
                        <span>Temp</span>
                        <span class="stat-value">${temp}°C</span>
                    </div>
                    <div class="progress-bar">
                        <div class="fill auto ${memClass}" style="width:${memPct}%"></div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // ─── Ollama Models ───────────────────────────────────────────────
    function renderOllama(data) {
        if (!els.ollamaBody) return;
        const models = data.models || [];
        if (models.length === 0) {
            els.ollamaBody.innerHTML = '<p class="loading-placeholder">No models loaded</p>';
            return;
        }
        els.ollamaBody.innerHTML = models.map(m => {
            const name = escapeHtml(m.name || m.model || '?');
            const size = m.size ? formatBytes(m.size) : '';
            const modified = m.modified_at ? new Date(m.modified_at).toLocaleDateString() : '';
            return `
                <div class="model-item fade-in">
                    <span class="model-name">${name}</span>
                    <span class="model-meta">${size} ${modified}</span>
                </div>
            `;
        }).join('');
    }

    // ─── Services ────────────────────────────────────────────────────
    function renderServices(data) {
        if (!els.servicesBody) return;
        const svcs = data.services || data || [];
        const list = Array.isArray(svcs) ? svcs : Object.entries(svcs).map(([k, v]) => ({
            name: k, status: typeof v === 'string' ? v : (v.status || 'unknown'),
        }));

        if (list.length === 0) {
            els.servicesBody.innerHTML = '<p class="loading-placeholder">No services</p>';
            return;
        }

        els.servicesBody.innerHTML = list.map(s => {
            const name = escapeHtml(s.name || s.service || '?');
            const active = (s.status === 'active' || s.status === 'running' || s.status === 'healthy');
            const cls = active ? 'active' : 'inactive';
            const icon = active ? '●' : '○';
            return `
                <div class="service-row fade-in">
                    <span class="service-name">${name}</span>
                    <span class="service-status ${cls}">${icon} ${escapeHtml(s.status || 'unknown')}</span>
                </div>
            `;
        }).join('');
    }

    // ─── Tasks ───────────────────────────────────────────────────────
    function renderTasks(data) {
        if (!els.tasksBody) return;
        const tasks = data.tasks || data || [];
        const list = Array.isArray(tasks) ? tasks : [];

        if (els.taskCount) {
            els.taskCount.textContent = list.length;
        }

        if (list.length === 0) {
            els.tasksBody.innerHTML = '<p class="loading-placeholder">No active tasks</p>';
            return;
        }

        // Show most recent first, limit to 20
        const shown = list.slice(0, 20);
        els.tasksBody.innerHTML = shown.map(t => {
            const status = (t.status || 'pending').toLowerCase();
            const title = escapeHtml(t.title || t.name || t.description || '?');
            const agent = t.agent ? escapeHtml(t.agent) : '';
            const created = t.created ? new Date(t.created).toLocaleString() : '';
            return `
                <div class="task-item ${status} fade-in">
                    <div class="task-title">${title}</div>
                    <div class="task-meta">${agent} ${created}</div>
                </div>
            `;
        }).join('');
    }

    // ─── Resources ───────────────────────────────────────────────────
    function renderResources(data) {
        if (!els.resBody) return;

        const cpu = data.cpu_percent || data.cpu || 0;
        const mem = data.memory_percent || data.memory || 0;
        const disk = data.disk_percent || data.disk || 0;

        const cpuClass = cpu > 85 ? 'danger' : cpu > 60 ? 'warn' : '';
        const memClass = mem > 85 ? 'danger' : mem > 60 ? 'warn' : '';
        const diskClass = disk > 85 ? 'danger' : disk > 60 ? 'warn' : '';

        els.resBody.innerHTML = `
            <div class="resource-row fade-in">
                <div class="resource-label">
                    <span class="label-name">CPU</span>
                    <span class="label-value">${formatPercent(cpu)}</span>
                </div>
                <div class="progress-bar"><div class="fill auto ${cpuClass}" style="width:${cpu}%"></div></div>
            </div>
            <div class="resource-row fade-in">
                <div class="resource-label">
                    <span class="label-name">Memory</span>
                    <span class="label-value">${formatPercent(mem)}</span>
                </div>
                <div class="progress-bar"><div class="fill auto ${memClass}" style="width:${mem}%"></div></div>
            </div>
            <div class="resource-row fade-in">
                <div class="resource-label">
                    <span class="label-name">Disk</span>
                    <span class="label-value">${formatPercent(disk)}</span>
                </div>
                <div class="progress-bar"><div class="fill auto ${diskClass}" style="width:${disk}%"></div></div>
            </div>
        `;
    }

    // ─── Runner ──────────────────────────────────────────────────────
    function renderRunner(data) {
        if (!els.runnerBody) return;

        const status = data.status || data.state || 'unknown';
        const running = (status === 'online' || status === 'running' || status === 'active' || status === 'idle');
        const dot = running ? 'running' : 'stopped';
        const name = escapeHtml(data.name || 'slate-runner');
        const labels = (data.labels || []).map(escapeHtml).join(', ') || 'self-hosted, slate';
        const workflows = data.active_workflows || data.active_runs || 0;

        els.runnerBody.innerHTML = `
            <div class="runner-status fade-in">
                <span class="runner-dot ${dot}"></span>
                <span style="font-family:var(--font-mono);font-size:0.85rem">${name}</span>
                <span style="margin-left:auto;color:var(--text-dim);font-size:0.75rem">${escapeHtml(status)}</span>
            </div>
            <div style="font-size:0.75rem;color:var(--text-secondary);padding:4px 0">
                Labels: ${labels}
            </div>
            <div style="font-size:0.75rem;color:var(--text-secondary);padding:2px 0">
                Active workflows: <span style="color:var(--olympus-gold);font-family:var(--font-mono)">${workflows}</span>
            </div>
        `;
    }

    // ─── Refresh buttons ─────────────────────────────────────────────
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-refresh');
        if (!btn) return;
        const target = btn.dataset.target;
        if (target === 'graph' && window.AthenaGraph) {
            window.AthenaGraph.refresh();
        } else if (target === 'all') {
            pollAll();
        }
    });

    // ─── Init ────────────────────────────────────────────────────────
    connectWS();
    pollAll();
    setInterval(pollAll, POLL_INTERVAL);

})();
