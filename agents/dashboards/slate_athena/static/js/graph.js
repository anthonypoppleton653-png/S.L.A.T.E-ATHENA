/* SLATE-ATHENA — D3.js Force-Directed System Topology
 * Modified: 2026-02-10T01:30:00Z | Author: COPILOT | Change: Create D3.js force graph with Greek-themed node colors
 *
 * Fetches /api/graph for { nodes, links } and renders an interactive
 * force-directed layout inside #systemGraph.
 */

(function () {
    'use strict';

    // ─── Color palette by node group ────────────────────────────────
    const GROUP_COLORS = {
        core:     '#8E44AD',  // Tyrian Purple
        ui:       '#C768A2',  // Tyrian Light
        ai:       '#D4AC0D',  // Olympus Gold
        data:     '#2980B9',  // Aegean Blue
        ci:       '#27AE60',  // Olive Green
        hardware: '#E67E22',  // Bronze
        infra:    '#2E4053',  // Parthenon Stone
        default:  '#546E7A',  // Dim gray
    };

    const container = document.getElementById('systemGraph');
    if (!container) return;

    let svg, simulation, linkGroup, nodeGroup, labelGroup;
    let width, height;

    // ─── Build the SVG ───────────────────────────────────────────────
    function initSVG() {
        width = container.clientWidth || 600;
        height = container.clientHeight || 500;

        svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${width} ${height}`)
            .attr('preserveAspectRatio', 'xMidYMid meet');

        // Defs: arrow marker for directed links
        const defs = svg.append('defs');
        defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 22)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#2E4053');

        // Radial gradient for background glow
        const radGrad = defs.append('radialGradient')
            .attr('id', 'bgGlow')
            .attr('cx', '50%').attr('cy', '50%')
            .attr('r', '50%');
        radGrad.append('stop').attr('offset', '0%').attr('stop-color', 'rgba(142,68,173,0.06)');
        radGrad.append('stop').attr('offset', '100%').attr('stop-color', 'transparent');

        svg.append('rect')
            .attr('width', width)
            .attr('height', height)
            .attr('fill', 'url(#bgGlow)');

        linkGroup = svg.append('g').attr('class', 'links');
        nodeGroup = svg.append('g').attr('class', 'nodes');
        labelGroup = svg.append('g').attr('class', 'labels');
    }

    // ─── Fetch data and render ───────────────────────────────────────
    async function loadGraph() {
        let data;
        try {
            const resp = await fetch('/api/graph');
            if (!resp.ok) throw new Error(resp.statusText);
            data = await resp.json();
        } catch (err) {
            console.warn('[graph] Fetch failed, using fallback data:', err);
            data = fallbackData();
        }

        render(data);
    }

    // ─── Render force layout ─────────────────────────────────────────
    function render(data) {
        const nodes = data.nodes || [];
        const links = (data.links || []).map(l => ({
            source: typeof l.source === 'string' ? l.source : l.source,
            target: typeof l.target === 'string' ? l.target : l.target,
            value: l.value || 1,
        }));

        simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(90))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30))
            .on('tick', ticked);

        // Links
        const link = linkGroup.selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('stroke', '#2E4053')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.max(1, d.value))
            .attr('marker-end', 'url(#arrowhead)');

        // Node circles
        const node = nodeGroup.selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('r', d => d.size || 10)
            .attr('fill', d => GROUP_COLORS[d.group] || GROUP_COLORS.default)
            .attr('stroke', '#0C1219')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .call(drag(simulation));

        // Hover glow
        node.on('mouseover', function (event, d) {
            d3.select(this)
                .transition().duration(200)
                .attr('r', (d.size || 10) + 4)
                .attr('stroke', GROUP_COLORS[d.group] || GROUP_COLORS.default)
                .attr('stroke-width', 3);
            showTooltip(event, d);
        }).on('mouseout', function (event, d) {
            d3.select(this)
                .transition().duration(200)
                .attr('r', d.size || 10)
                .attr('stroke', '#0C1219')
                .attr('stroke-width', 2);
            hideTooltip();
        });

        // Labels
        const label = labelGroup.selectAll('text')
            .data(nodes)
            .enter().append('text')
            .text(d => d.label || d.id)
            .attr('font-size', '9px')
            .attr('font-family', "'JetBrains Mono', monospace")
            .attr('fill', '#8395A7')
            .attr('text-anchor', 'middle')
            .attr('dy', d => (d.size || 10) + 14)
            .style('pointer-events', 'none');

        function ticked() {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x = clamp(d.x, 20, width - 20))
                .attr('cy', d => d.y = clamp(d.y, 20, height - 20));

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }
    }

    function clamp(val, min, max) { return Math.max(min, Math.min(max, val)); }

    // ─── Drag behavior ───────────────────────────────────────────────
    function drag(sim) {
        function dragstarted(event) {
            if (!event.active) sim.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }
        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        function dragended(event) {
            if (!event.active) sim.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }

    // ─── Tooltip ─────────────────────────────────────────────────────
    let tooltip;

    function showTooltip(event, d) {
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.style.cssText = `
                position: fixed; padding: 8px 12px; border-radius: 4px;
                background: #141C28; border: 1px solid #2E4053;
                color: #E8E0D0; font-size: 12px; font-family: 'JetBrains Mono', monospace;
                pointer-events: none; z-index: 999; max-width: 220px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            `;
            document.body.appendChild(tooltip);
        }
        let html = `<strong style="color:${GROUP_COLORS[d.group] || '#8395A7'}">${escapeHtml(d.label || d.id)}</strong>`;
        if (d.status) html += `<br>Status: ${escapeHtml(d.status)}`;
        if (d.port)   html += `<br>Port: ${d.port}`;
        if (d.group)  html += `<br>Group: ${escapeHtml(d.group)}`;
        tooltip.innerHTML = html;
        tooltip.style.display = 'block';
        tooltip.style.left = (event.clientX + 14) + 'px';
        tooltip.style.top = (event.clientY - 10) + 'px';
    }

    function hideTooltip() {
        if (tooltip) tooltip.style.display = 'none';
    }

    function escapeHtml(s) {
        const el = document.createElement('span');
        el.textContent = s;
        return el.innerHTML;
    }

    // ─── Resize handler ──────────────────────────────────────────────
    function onResize() {
        if (!svg) return;
        width = container.clientWidth || 600;
        height = container.clientHeight || 500;
        svg.attr('viewBox', `0 0 ${width} ${height}`);
        if (simulation) {
            simulation.force('center', d3.forceCenter(width / 2, height / 2));
            simulation.alpha(0.3).restart();
        }
    }

    window.addEventListener('resize', debounce(onResize, 250));

    function debounce(fn, ms) {
        let t;
        return function (...args) {
            clearTimeout(t);
            t = setTimeout(() => fn.apply(this, args), ms);
        };
    }

    // ─── Fallback data (offline mode) ────────────────────────────────
    function fallbackData() {
        return {
            nodes: [
                { id: 'core',        label: 'SLATE Core',       group: 'core',     size: 16 },
                { id: 'dashboard',   label: 'Dashboard',        group: 'ui',       size: 12 },
                { id: 'athena',      label: 'Athena UI',        group: 'ui',       size: 12 },
                { id: 'ollama',      label: 'Ollama',           group: 'ai',       size: 14, port: 11434 },
                { id: 'chromadb',    label: 'ChromaDB',         group: 'data',     size: 12, port: 8000 },
                { id: 'runner',      label: 'GitHub Runner',    group: 'ci',       size: 12 },
                { id: 'gpu0',        label: 'RTX 5070 Ti #0',   group: 'hardware', size: 13 },
                { id: 'gpu1',        label: 'RTX 5070 Ti #1',   group: 'hardware', size: 13 },
                { id: 'k8s',         label: 'Kubernetes',       group: 'infra',    size: 14 },
                { id: 'workflow',    label: 'Workflow Mgr',     group: 'core',     size: 10 },
                { id: 'autonomous',  label: 'Autonomous Loop',  group: 'ai',       size: 11 },
                { id: 'bridge',      label: 'Copilot Bridge',   group: 'infra',    size: 10 },
            ],
            links: [
                { source: 'core', target: 'dashboard' },
                { source: 'core', target: 'athena' },
                { source: 'core', target: 'ollama' },
                { source: 'core', target: 'chromadb' },
                { source: 'core', target: 'runner' },
                { source: 'core', target: 'workflow' },
                { source: 'core', target: 'k8s' },
                { source: 'ollama', target: 'gpu0', value: 2 },
                { source: 'ollama', target: 'gpu1', value: 2 },
                { source: 'k8s', target: 'bridge' },
                { source: 'autonomous', target: 'ollama' },
                { source: 'autonomous', target: 'bridge' },
                { source: 'workflow', target: 'runner' },
            ],
        };
    }

    // ─── Public refresh (called from main.js) ────────────────────────
    window.AthenaGraph = {
        refresh: async function () {
            if (svg) {
                linkGroup.selectAll('*').remove();
                nodeGroup.selectAll('*').remove();
                labelGroup.selectAll('*').remove();
                if (simulation) simulation.stop();
            }
            await loadGraph();
        },
    };

    // ─── Init ────────────────────────────────────────────────────────
    initSVG();
    loadGraph();
})();
