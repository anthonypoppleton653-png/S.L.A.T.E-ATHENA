#!/usr/bin/env python3
# Modified: 2026-02-09T05:30:00Z | Author: Claude | Change: D3.js force-directed tech tree visualization
"""
SLATE Tech Tree Visualization Component
========================================
D3.js force-directed graph visualization for the SLATE tech tree.

Features:
- Force-directed layout with physics simulation
- Status-based node coloring (complete, in_progress, available)
- Phase-based node sizing
- Interactive zoom and pan
- Hover tooltips with node details
- Click to highlight connected nodes
- Real-time data from /api/tech-tree

Follows Watchmaker design philosophy:
- Gear icons for active nodes
- Jewel status indicators
- Flow lines for edges
- Glassmorphism cards
"""

import json
from pathlib import Path


def generate_tech_tree_styles() -> str:
    """Generate CSS styles for tech tree visualization."""
    return """
/* Tech Tree Visualization */
.tech-tree-container {
    width: 100%;
    height: 500px;
    background: var(--sl-bg-surface);
    border-radius: var(--sl-radius-lg);
    overflow: hidden;
    position: relative;
}

.tech-tree-svg {
    width: 100%;
    height: 100%;
}

/* Node styling */
.tech-node {
    cursor: pointer;
    transition: all var(--sl-duration-fast) var(--sl-ease-standard);
}

.tech-node:hover {
    filter: brightness(1.2);
}

.tech-node circle {
    stroke-width: 2px;
    transition: all var(--sl-duration-fast) var(--sl-ease-standard);
}

.tech-node.status-complete circle {
    fill: var(--sl-success);
    stroke: var(--sl-success);
}

.tech-node.status-in_progress circle {
    fill: var(--sl-warning);
    stroke: var(--sl-warning);
    animation: pulse-glow 2s ease-in-out infinite;
}

.tech-node.status-available circle {
    fill: var(--sl-info);
    stroke: var(--sl-info);
}

.tech-node.status-locked circle {
    fill: var(--sl-text-disabled);
    stroke: var(--sl-text-tertiary);
}

.tech-node text {
    fill: var(--sl-text-primary);
    font-size: 10px;
    font-family: var(--sl-font-mono);
    pointer-events: none;
    text-anchor: middle;
}

/* Edge styling */
.tech-edge {
    stroke: var(--sl-border-variant);
    stroke-width: 1.5px;
    fill: none;
    opacity: 0.6;
}

.tech-edge.active {
    stroke: var(--sl-accent);
    stroke-width: 2px;
    opacity: 1;
    stroke-dasharray: 5, 3;
    animation: flow-dash 1s linear infinite;
}

/* Tooltip */
.tech-tooltip {
    position: absolute;
    background: var(--sl-glass-bg-elevated);
    backdrop-filter: blur(var(--sl-glass-blur));
    border: 1px solid var(--sl-glass-border);
    border-radius: var(--sl-radius-md);
    padding: var(--sl-space-3);
    pointer-events: none;
    opacity: 0;
    transition: opacity var(--sl-duration-fast) var(--sl-ease-standard);
    z-index: 1000;
    max-width: 300px;
}

.tech-tooltip.visible {
    opacity: 1;
}

.tech-tooltip-title {
    font-weight: 600;
    color: var(--sl-text-primary);
    margin-bottom: var(--sl-space-1);
}

.tech-tooltip-status {
    display: inline-block;
    padding: 2px 8px;
    border-radius: var(--sl-radius-full);
    font-size: 10px;
    text-transform: uppercase;
    margin-bottom: var(--sl-space-2);
}

.tech-tooltip-status.complete { background: var(--sl-success-container); color: var(--sl-success); }
.tech-tooltip-status.in_progress { background: var(--sl-warning-container); color: var(--sl-warning); }
.tech-tooltip-status.available { background: var(--sl-info-container); color: var(--sl-info); }

.tech-tooltip-desc {
    font-size: 12px;
    color: var(--sl-text-secondary);
    line-height: 1.4;
}

/* Legend */
.tech-legend {
    position: absolute;
    bottom: var(--sl-space-3);
    left: var(--sl-space-3);
    display: flex;
    gap: var(--sl-space-3);
    background: var(--sl-glass-bg);
    backdrop-filter: blur(var(--sl-glass-blur));
    padding: var(--sl-space-2) var(--sl-space-3);
    border-radius: var(--sl-radius-sm);
    border: 1px solid var(--sl-glass-border);
}

.tech-legend-item {
    display: flex;
    align-items: center;
    gap: var(--sl-space-1);
    font-size: 10px;
    color: var(--sl-text-secondary);
}

.tech-legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.tech-legend-dot.complete { background: var(--sl-success); }
.tech-legend-dot.in_progress { background: var(--sl-warning); }
.tech-legend-dot.available { background: var(--sl-info); }

/* Animations */
@keyframes pulse-glow {
    0%, 100% { filter: drop-shadow(0 0 4px currentColor); }
    50% { filter: drop-shadow(0 0 12px currentColor); }
}

@keyframes flow-dash {
    to { stroke-dashoffset: -8; }
}

/* Controls */
.tech-tree-controls {
    position: absolute;
    top: var(--sl-space-3);
    right: var(--sl-space-3);
    display: flex;
    gap: var(--sl-space-2);
}

.tech-tree-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--sl-glass-bg);
    border: 1px solid var(--sl-glass-border);
    border-radius: var(--sl-radius-sm);
    color: var(--sl-text-secondary);
    cursor: pointer;
    transition: all var(--sl-duration-fast) var(--sl-ease-standard);
}

.tech-tree-btn:hover {
    background: var(--sl-glass-bg-elevated);
    color: var(--sl-text-primary);
    border-color: var(--sl-glass-border-hover);
}
"""


def generate_tech_tree_script() -> str:
    """Generate D3.js tech tree visualization script."""
    return """
// Tech Tree Visualization using D3.js force-directed graph
class TechTreeViz {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        this.nodes = [];
        this.edges = [];
        this.simulation = null;

        this.init();
    }

    init() {
        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('class', 'tech-tree-svg')
            .attr('viewBox', [0, 0, this.width, this.height]);

        // Create groups for edges and nodes (edges behind nodes)
        this.edgeGroup = this.svg.append('g').attr('class', 'edges');
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');

        // Create tooltip
        this.tooltip = d3.select(this.container)
            .append('div')
            .attr('class', 'tech-tooltip');

        // Create legend
        this.createLegend();

        // Create controls
        this.createControls();

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on('zoom', (event) => {
                this.edgeGroup.attr('transform', event.transform);
                this.nodeGroup.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Load data
        this.loadData();
    }

    createLegend() {
        const legend = document.createElement('div');
        legend.className = 'tech-legend';
        legend.innerHTML = `
            <div class="tech-legend-item"><div class="tech-legend-dot complete"></div>Complete</div>
            <div class="tech-legend-item"><div class="tech-legend-dot in_progress"></div>In Progress</div>
            <div class="tech-legend-item"><div class="tech-legend-dot available"></div>Available</div>
        `;
        this.container.appendChild(legend);
    }

    createControls() {
        const controls = document.createElement('div');
        controls.className = 'tech-tree-controls';
        controls.innerHTML = `
            <button class="tech-tree-btn" onclick="techTreeViz.resetZoom()" title="Reset zoom">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
                </svg>
            </button>
            <button class="tech-tree-btn" onclick="techTreeViz.loadData()" title="Refresh">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                    <path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
                    <path d="M16 21h5v-5"/>
                </svg>
            </button>
        `;
        this.container.appendChild(controls);
    }

    async loadData() {
        try {
            const response = await fetch('/api/tech-tree');
            const data = await response.json();

            if (data.nodes && data.edges) {
                this.nodes = data.nodes.map(n => ({
                    ...n,
                    x: this.width / 2 + (Math.random() - 0.5) * 200,
                    y: this.height / 2 + (Math.random() - 0.5) * 200
                }));
                this.edges = data.edges.map(e => ({
                    source: e.from,
                    target: e.to
                }));
                this.render();
            }
        } catch (e) {
            console.error('Failed to load tech tree:', e);
        }
    }

    render() {
        // Create force simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.edges)
                .id(d => d.id)
                .distance(100)
                .strength(0.5))
            .force('charge', d3.forceManyBody()
                .strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(40));

        // Render edges
        const edges = this.edgeGroup.selectAll('.tech-edge')
            .data(this.edges)
            .join('line')
            .attr('class', d => 'tech-edge');

        // Render nodes
        const nodes = this.nodeGroup.selectAll('.tech-node')
            .data(this.nodes)
            .join('g')
            .attr('class', d => `tech-node status-${d.status}`)
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d)));

        // Add circles to nodes
        nodes.append('circle')
            .attr('r', d => d.phase === 1 ? 20 : 16);

        // Add labels
        nodes.append('text')
            .attr('dy', 30)
            .text(d => d.name.length > 12 ? d.name.substring(0, 12) + '...' : d.name);

        // Add hover events
        nodes.on('mouseenter', (event, d) => this.showTooltip(event, d))
            .on('mouseleave', () => this.hideTooltip())
            .on('click', (event, d) => this.highlightConnections(d));

        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            edges
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodes.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    }

    showTooltip(event, d) {
        const rect = this.container.getBoundingClientRect();
        this.tooltip.html(`
            <div class="tech-tooltip-title">${d.name}</div>
            <span class="tech-tooltip-status ${d.status}">${d.status.replace('_', ' ')}</span>
            <div class="tech-tooltip-desc">${d.description || ''}</div>
        `)
        .style('left', (event.clientX - rect.left + 10) + 'px')
        .style('top', (event.clientY - rect.top - 10) + 'px')
        .classed('visible', true);
    }

    hideTooltip() {
        this.tooltip.classed('visible', false);
    }

    highlightConnections(node) {
        const connectedIds = new Set([node.id]);
        this.edges.forEach(e => {
            if (e.source.id === node.id) connectedIds.add(e.target.id);
            if (e.target.id === node.id) connectedIds.add(e.source.id);
        });

        this.nodeGroup.selectAll('.tech-node')
            .style('opacity', d => connectedIds.has(d.id) ? 1 : 0.3);

        this.edgeGroup.selectAll('.tech-edge')
            .classed('active', d => d.source.id === node.id || d.target.id === node.id)
            .style('opacity', d => (d.source.id === node.id || d.target.id === node.id) ? 1 : 0.2);

        // Reset after delay
        setTimeout(() => {
            this.nodeGroup.selectAll('.tech-node').style('opacity', 1);
            this.edgeGroup.selectAll('.tech-edge')
                .classed('active', false)
                .style('opacity', 0.6);
        }, 3000);
    }

    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    resetZoom() {
        this.svg.transition()
            .duration(500)
            .call(d3.zoom().transform, d3.zoomIdentity);
    }
}

// Initialize when container exists
let techTreeViz = null;
function initTechTree() {
    if (document.getElementById('tech-tree-viz')) {
        techTreeViz = new TechTreeViz('tech-tree-viz');
    }
}
"""


def generate_tech_tree_html() -> str:
    """Generate HTML for tech tree visualization card."""
    return """
<div class="card col-12">
    <div class="card-header">
        <span class="card-title">Tech Tree Visualization</span>
        <span class="card-subtitle">Force-directed dependency graph</span>
    </div>
    <div class="tech-tree-container" id="tech-tree-viz"></div>
</div>
"""


def generate_d3_script_tag() -> str:
    """Generate D3.js script include."""
    return '<script src="https://d3js.org/d3.v7.min.js"></script>'


if __name__ == "__main__":
    print("Tech Tree Visualization Component")
    print("=" * 50)
    print("\nStyles:")
    print(generate_tech_tree_styles()[:500] + "...")
    print("\nHTML:")
    print(generate_tech_tree_html())
    print("\nD3 Script Tag:")
    print(generate_d3_script_tag())
