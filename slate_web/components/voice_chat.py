#!/usr/bin/env python3
# Modified: 2026-02-10T05:35:00Z | Author: COPILOT | Change: Initial creation of voice chat UI component
"""
Voice Chat UI Component for SLATE Dashboard.

Generates the HTML/CSS/JS for a WebRTC voice chat widget that integrates
into the SLATE dashboard. Uses the signaling server at /ws/voice/{room_id}.

Features:
- Room join/leave with display name
- WebRTC peer connections with audio tracks
- Mute/unmute toggle
- Peer list with connection state indicators
- ICE connection state monitoring and logging
- Audio level visualization
- Automatic peer connection setup (mesh topology)
- Graceful error handling with user feedback
"""

# Modified: 2026-02-10T05:35:00Z | Author: COPILOT | Change: Voice chat UI with WebRTC, STUN/TURN, ICE diagnostics


def generate_voice_chat_css() -> str:
    """Generate CSS for the voice chat component."""
    return """
/* ── Voice Chat Component ──────────────────────────────────────────────── */

#voice-chat-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 10000;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

#voice-chat-toggle {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: 2px solid rgba(0, 200, 255, 0.4);
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #00c8ff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(0, 200, 255, 0.15);
    transition: all 0.3s ease;
}

#voice-chat-toggle:hover {
    border-color: #00c8ff;
    box-shadow: 0 4px 30px rgba(0, 200, 255, 0.3);
    transform: scale(1.05);
}

#voice-chat-toggle.active {
    background: linear-gradient(135deg, #00c8ff 0%, #0098cc 100%);
    color: #0a0a1a;
    border-color: #00c8ff;
}

#voice-chat-toggle svg {
    width: 24px;
    height: 24px;
    fill: currentColor;
}

#voice-chat-panel {
    display: none;
    position: absolute;
    bottom: 70px;
    right: 0;
    width: 320px;
    max-height: 500px;
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border: 1px solid rgba(0, 200, 255, 0.2);
    border-radius: 12px;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
    overflow: hidden;
}

#voice-chat-panel.open {
    display: flex;
    flex-direction: column;
}

.vc-header {
    padding: 12px 16px;
    background: rgba(0, 200, 255, 0.05);
    border-bottom: 1px solid rgba(0, 200, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.vc-header h3 {
    margin: 0;
    font-size: 14px;
    color: #e0e0e0;
    font-weight: 600;
}

.vc-header .vc-status {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    background: rgba(100, 100, 100, 0.3);
    color: #888;
}

.vc-header .vc-status.connected {
    background: rgba(0, 200, 100, 0.15);
    color: #00c864;
}

.vc-join-form {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.vc-join-form input {
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    color: #e0e0e0;
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s;
}

.vc-join-form input:focus {
    border-color: rgba(0, 200, 255, 0.5);
}

.vc-join-form input::placeholder {
    color: #555;
}

.vc-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
}

.vc-btn-join {
    background: linear-gradient(135deg, #00c8ff 0%, #0098cc 100%);
    color: #0a0a1a;
}

.vc-btn-join:hover {
    box-shadow: 0 2px 12px rgba(0, 200, 255, 0.3);
}

.vc-btn-leave {
    background: rgba(255, 80, 80, 0.2);
    color: #ff5050;
    border: 1px solid rgba(255, 80, 80, 0.3);
}

.vc-btn-leave:hover {
    background: rgba(255, 80, 80, 0.3);
}

.vc-btn-mute {
    background: rgba(255, 255, 255, 0.05);
    color: #aaa;
    border: 1px solid rgba(255, 255, 255, 0.1);
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
}

.vc-btn-mute.muted {
    background: rgba(255, 80, 80, 0.2);
    color: #ff5050;
    border-color: rgba(255, 80, 80, 0.3);
}

.vc-room-view {
    display: none;
    flex-direction: column;
    flex: 1;
    min-height: 0;
}

.vc-room-view.active {
    display: flex;
}

.vc-room-info {
    padding: 8px 16px;
    font-size: 11px;
    color: #666;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.vc-peers {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    max-height: 250px;
}

.vc-peer {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 4px;
    background: rgba(255, 255, 255, 0.02);
    transition: background 0.2s;
}

.vc-peer:hover {
    background: rgba(255, 255, 255, 0.05);
}

.vc-peer-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #00c8ff 0%, #7b2ff7 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 600;
    color: white;
    flex-shrink: 0;
}

.vc-peer-info {
    flex: 1;
    min-width: 0;
}

.vc-peer-name {
    font-size: 13px;
    color: #e0e0e0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.vc-peer-state {
    font-size: 10px;
    color: #666;
}

.vc-peer-state.connected { color: #00c864; }
.vc-peer-state.connecting { color: #ffaa00; }
.vc-peer-state.failed { color: #ff5050; }

.vc-peer .vc-audio-level {
    width: 4px;
    height: 20px;
    background: rgba(0, 200, 100, 0.2);
    border-radius: 2px;
    overflow: hidden;
    flex-shrink: 0;
}

.vc-peer .vc-audio-level-bar {
    width: 100%;
    background: #00c864;
    border-radius: 2px;
    transition: height 0.1s;
    position: relative;
    bottom: 0;
}

.vc-peer.muted .vc-peer-avatar {
    opacity: 0.5;
}

.vc-controls {
    padding: 12px 16px;
    display: flex;
    gap: 8px;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.vc-controls .vc-btn-leave {
    flex: 1;
}

.vc-log {
    max-height: 80px;
    overflow-y: auto;
    padding: 4px 12px;
    font-size: 10px;
    color: #555;
    border-top: 1px solid rgba(255, 255, 255, 0.03);
    font-family: 'Cascadia Code', 'Consolas', monospace;
}

.vc-log div {
    padding: 1px 0;
}

.vc-log .vc-log-error { color: #ff5050; }
.vc-log .vc-log-ok { color: #00c864; }
.vc-log .vc-log-ice { color: #ffaa00; }
"""


def generate_voice_chat_html() -> str:
    """Generate HTML for the voice chat widget."""
    return """
<!-- Voice Chat Widget -->
<div id="voice-chat-widget">
    <button id="voice-chat-toggle" onclick="voiceChat.togglePanel()" title="Voice Chat">
        <svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
    </button>

    <div id="voice-chat-panel">
        <div class="vc-header">
            <h3>Voice Chat</h3>
            <span id="vc-status" class="vc-status">Disconnected</span>
        </div>

        <!-- Join Form -->
        <div id="vc-join-form" class="vc-join-form">
            <input type="text" id="vc-room-input" placeholder="Room name (e.g. slate-dev)" value="slate-dev" />
            <input type="text" id="vc-name-input" placeholder="Your display name" value="" />
            <button class="vc-btn vc-btn-join" onclick="voiceChat.joinRoom()">Join Room</button>
        </div>

        <!-- Room View -->
        <div id="vc-room-view" class="vc-room-view">
            <div id="vc-room-info" class="vc-room-info"></div>
            <div id="vc-peers" class="vc-peers"></div>
            <div class="vc-controls">
                <button id="vc-mute-btn" class="vc-btn vc-btn-mute" onclick="voiceChat.toggleMute()" title="Toggle Mute">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/></svg>
                </button>
                <button class="vc-btn vc-btn-leave" onclick="voiceChat.leaveRoom()">Leave Room</button>
            </div>
            <div id="vc-log" class="vc-log"></div>
        </div>
    </div>
</div>
"""


def generate_voice_chat_js() -> str:
    """Generate JavaScript for the voice chat component with full WebRTC handling."""
    return """
// ── Voice Chat Controller ──────────────────────────────────────────────────
// Modified: 2026-02-10T05:35:00Z | Author: COPILOT | Change: WebRTC voice chat with signaling, ICE diagnostics, audio tracks

const voiceChat = (() => {
    // State
    let ws = null;
    let myPeerId = null;
    let roomId = null;
    let isMuted = false;
    let localStream = null;
    let iceServers = [];

    // Map of peer_id -> { pc: RTCPeerConnection, audioEl: HTMLAudioElement, state: string }
    const peerConnections = {};

    // ── UI Helpers ─────────────────────────────────────────────────────────

    function log(msg, cls = '') {
        const el = document.getElementById('vc-log');
        if (!el) return;
        const div = document.createElement('div');
        if (cls) div.className = 'vc-log-' + cls;
        div.textContent = new Date().toLocaleTimeString() + ' ' + msg;
        el.appendChild(div);
        el.scrollTop = el.scrollHeight;
        // Keep max 50 lines
        while (el.children.length > 50) el.removeChild(el.firstChild);
    }

    function setStatus(text, connected = false) {
        const el = document.getElementById('vc-status');
        if (el) {
            el.textContent = text;
            el.className = 'vc-status' + (connected ? ' connected' : '');
        }
    }

    function showJoinForm() {
        const f = document.getElementById('vc-join-form');
        const r = document.getElementById('vc-room-view');
        if (f) f.style.display = 'flex';
        if (r) r.classList.remove('active');
        setStatus('Disconnected');
        document.getElementById('voice-chat-toggle')?.classList.remove('active');
    }

    function showRoomView() {
        const f = document.getElementById('vc-join-form');
        const r = document.getElementById('vc-room-view');
        if (f) f.style.display = 'none';
        if (r) r.classList.add('active');
        document.getElementById('voice-chat-toggle')?.classList.add('active');
    }

    function renderPeers(peers) {
        const el = document.getElementById('vc-peers');
        if (!el) return;
        el.innerHTML = '';
        peers.forEach(p => {
            const pc = peerConnections[p.peer_id];
            const state = pc ? pc.state : (p.peer_id === myPeerId ? 'you' : 'new');
            const isSelf = p.peer_id === myPeerId;
            const initial = (p.display_name || '?')[0].toUpperCase();

            el.innerHTML += `
                <div class="vc-peer ${p.is_muted ? 'muted' : ''}" data-peer="${p.peer_id}">
                    <div class="vc-peer-avatar">${initial}</div>
                    <div class="vc-peer-info">
                        <div class="vc-peer-name">${p.display_name || 'Anonymous'}${isSelf ? ' (you)' : ''}</div>
                        <div class="vc-peer-state ${state}">${state}</div>
                    </div>
                    <div class="vc-audio-level"><div class="vc-audio-level-bar" style="height: 0%"></div></div>
                </div>
            `;
        });
    }

    function updateRoomInfo() {
        const el = document.getElementById('vc-room-info');
        if (el && roomId) {
            const count = Object.keys(peerConnections).length + 1;
            el.textContent = `Room: ${roomId} · ${count} peer${count !== 1 ? 's' : ''}`;
        }
    }

    // ── Audio ──────────────────────────────────────────────────────────────

    async function getLocalAudio() {
        try {
            localStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
                video: false,
            });
            log('Microphone access granted', 'ok');
            return true;
        } catch (err) {
            log('Microphone error: ' + err.message, 'error');
            return false;
        }
    }

    function stopLocalAudio() {
        if (localStream) {
            localStream.getTracks().forEach(t => t.stop());
            localStream = null;
        }
    }

    // ── WebRTC Peer Connection ─────────────────────────────────────────────

    function createPeerConnection(remotePeerId) {
        const config = { iceServers: iceServers };
        const pc = new RTCPeerConnection(config);

        peerConnections[remotePeerId] = { pc, audioEl: null, state: 'connecting' };

        // Add our audio tracks to the connection
        if (localStream) {
            localStream.getTracks().forEach(track => {
                pc.addTrack(track, localStream);
            });
        }

        // Handle remote audio track
        pc.ontrack = (event) => {
            log(`Audio track received from peer ${remotePeerId}`, 'ok');
            const audio = new Audio();
            audio.srcObject = event.streams[0];
            audio.autoplay = true;
            audio.volume = 1.0;
            peerConnections[remotePeerId].audioEl = audio;
            audio.play().catch(e => log('Audio play error: ' + e.message, 'error'));
        };

        // ICE candidate events — relay to remote peer via signaling
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                log(`ICE candidate → ${remotePeerId}`, 'ice');
                sendSignal({
                    type: 'ice-candidate',
                    target_peer_id: remotePeerId,
                    candidate: event.candidate.toJSON(),
                });
            }
        };

        // ICE connection state monitoring (key diagnostic)
        pc.oniceconnectionstatechange = () => {
            const state = pc.iceConnectionState;
            log(`ICE state [${remotePeerId}]: ${state}`, state === 'connected' ? 'ok' : (state === 'failed' ? 'error' : 'ice'));
            if (peerConnections[remotePeerId]) {
                peerConnections[remotePeerId].state = state;
            }
            updateRoomInfo();

            if (state === 'failed') {
                log(`ICE failed for ${remotePeerId} — restarting`, 'error');
                pc.restartIce();
            }
            if (state === 'disconnected') {
                // Give 5s for recovery before cleanup
                setTimeout(() => {
                    if (pc.iceConnectionState === 'disconnected') {
                        log(`Peer ${remotePeerId} disconnected (timeout)`, 'error');
                    }
                }, 5000);
            }
        };

        // Peer connection state (overall)
        pc.onconnectionstatechange = () => {
            log(`Connection state [${remotePeerId}]: ${pc.connectionState}`);
            if (pc.connectionState === 'failed') {
                removePeerConnection(remotePeerId);
            }
        };

        return pc;
    }

    function removePeerConnection(peerId) {
        const entry = peerConnections[peerId];
        if (entry) {
            entry.pc.close();
            if (entry.audioEl) {
                entry.audioEl.srcObject = null;
                entry.audioEl = null;
            }
            delete peerConnections[peerId];
        }
        updateRoomInfo();
    }

    function closeAllPeerConnections() {
        Object.keys(peerConnections).forEach(removePeerConnection);
    }

    // ── Signaling ──────────────────────────────────────────────────────────

    function sendSignal(msg) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(msg));
        }
    }

    async function handleSignal(msg) {
        switch (msg.type) {

            case 'room_joined': {
                myPeerId = msg.peer_id;
                roomId = msg.room_id;
                iceServers = msg.ice_servers || [];
                log(`Joined room "${roomId}" as ${myPeerId}`, 'ok');
                log(`ICE servers: ${iceServers.length} configured`, 'ice');
                setStatus(`Room: ${roomId}`, true);
                showRoomView();
                renderPeers(msg.peers);
                updateRoomInfo();

                // Initiate connections to all existing peers (we are the offerer)
                for (const p of msg.peers) {
                    if (p.peer_id !== myPeerId) {
                        await initiateCall(p.peer_id);
                    }
                }
                break;
            }

            case 'peer_joined': {
                log(`${msg.display_name} joined (${msg.peer_id})`);
                // New peer will send us an offer — we wait
                updateRoomInfo();
                break;
            }

            case 'peer_left': {
                log(`${msg.display_name || msg.peer_id} left (${msg.reason})`);
                removePeerConnection(msg.peer_id);
                updateRoomInfo();
                break;
            }

            case 'offer': {
                log(`Offer from ${msg.from_peer_id}`, 'ice');
                const pc = createPeerConnection(msg.from_peer_id);
                await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                sendSignal({
                    type: 'answer',
                    target_peer_id: msg.from_peer_id,
                    sdp: pc.localDescription.toJSON(),
                });
                break;
            }

            case 'answer': {
                log(`Answer from ${msg.from_peer_id}`, 'ice');
                const entry = peerConnections[msg.from_peer_id];
                if (entry) {
                    await entry.pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
                }
                break;
            }

            case 'ice-candidate': {
                const entry = peerConnections[msg.from_peer_id];
                if (entry && msg.candidate) {
                    try {
                        await entry.pc.addIceCandidate(new RTCIceCandidate(msg.candidate));
                    } catch (e) {
                        log(`ICE add error: ${e.message}`, 'error');
                    }
                }
                break;
            }

            case 'peer_mute_changed': {
                log(`${msg.peer_id} ${msg.is_muted ? 'muted' : 'unmuted'}`);
                break;
            }

            case 'pong':
                break;

            case 'error':
                log(`Server: ${msg.message}`, 'error');
                break;

            default:
                log(`Unknown: ${msg.type}`);
        }
    }

    async function initiateCall(remotePeerId) {
        log(`Initiating call to ${remotePeerId}`, 'ice');
        const pc = createPeerConnection(remotePeerId);
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        sendSignal({
            type: 'offer',
            target_peer_id: remotePeerId,
            sdp: pc.localDescription.toJSON(),
        });
    }

    // ── Public API ─────────────────────────────────────────────────────────

    function togglePanel() {
        const panel = document.getElementById('voice-chat-panel');
        if (panel) panel.classList.toggle('open');
    }

    async function joinRoom() {
        const roomInput = document.getElementById('vc-room-input');
        const nameInput = document.getElementById('vc-name-input');
        const room = (roomInput?.value || 'slate-dev').trim();
        const name = (nameInput?.value || 'Anonymous').trim();

        if (!room) { log('Room name required', 'error'); return; }

        // Get microphone first
        const micOk = await getLocalAudio();
        if (!micOk) return;

        // Connect WebSocket for signaling
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${proto}//${location.host}/ws/voice/${encodeURIComponent(room)}?display_name=${encodeURIComponent(name)}`;

        setStatus('Connecting...');
        log(`Connecting to ${room}...`);

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            log('Signaling connected', 'ok');
        };

        ws.onmessage = async (event) => {
            try {
                const msg = JSON.parse(event.data);
                await handleSignal(msg);
            } catch (e) {
                log('Parse error: ' + e.message, 'error');
            }
        };

        ws.onclose = (event) => {
            log(`Signaling closed (${event.code}: ${event.reason || 'normal'})`, event.code === 1000 ? '' : 'error');
            cleanup();
        };

        ws.onerror = () => {
            log('Signaling connection error', 'error');
            setStatus('Error');
        };
    }

    function leaveRoom() {
        if (ws) {
            ws.close(1000, 'User left');
        }
        cleanup();
        log('Left room');
    }

    function cleanup() {
        closeAllPeerConnections();
        stopLocalAudio();
        ws = null;
        myPeerId = null;
        roomId = null;
        isMuted = false;
        showJoinForm();
        const muteBtn = document.getElementById('vc-mute-btn');
        if (muteBtn) muteBtn.classList.remove('muted');
    }

    function toggleMute() {
        if (!localStream) return;
        isMuted = !isMuted;
        localStream.getAudioTracks().forEach(t => { t.enabled = !isMuted; });
        const muteBtn = document.getElementById('vc-mute-btn');
        if (muteBtn) {
            muteBtn.classList.toggle('muted', isMuted);
            muteBtn.title = isMuted ? 'Unmute' : 'Mute';
        }
        sendSignal({ type: 'mute-toggle', is_muted: isMuted });
        log(isMuted ? 'Muted' : 'Unmuted');
    }

    // Keepalive ping
    setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            sendSignal({ type: 'ping' });
        }
    }, 25000);

    return { togglePanel, joinRoom, leaveRoom, toggleMute };
})();
"""


def generate_voice_chat_component() -> dict:
    """
    Return the complete voice chat component as a dict with CSS, HTML, and JS.

    Usage in dashboard:
        comp = generate_voice_chat_component()
        # Insert comp['css'] into <style>
        # Insert comp['html'] before </body>
        # Insert comp['js'] into <script>
    """
    return {
        "css": generate_voice_chat_css(),
        "html": generate_voice_chat_html(),
        "js": generate_voice_chat_js(),
    }
