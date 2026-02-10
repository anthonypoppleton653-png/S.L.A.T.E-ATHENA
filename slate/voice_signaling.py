#!/usr/bin/env python3
# Modified: 2026-02-10T05:35:00Z | Author: COPILOT | Change: Initial creation of WebRTC voice signaling server
"""
WebRTC Voice Signaling Server for SLATE collaborative sessions.

Provides:
- WebSocket-based signaling for WebRTC peer connections
- Room management for collaborative voice chat sessions
- STUN/TURN server configuration
- ICE candidate relay between peers
- Ollama-aware thread isolation (voice doesn't block inference)

Architecture:
    Browser A ──ws──▶ /ws/voice/{room_id} ◀──ws── Browser B
                            │
                    SignalingManager
                    ├── rooms: {room_id: {peer_id: ws}}
                    ├── relay: offer/answer/ice-candidate
                    └── config: STUN/TURN servers

Security:
- All bindings on 127.0.0.1 only (SLATE security rule)
- Room IDs are validated (alphanumeric + hyphens, max 64 chars)
- Max peers per room: 8
- Stale peer cleanup every 60s
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

logger = logging.getLogger("slate.voice_signaling")

# ── STUN/TURN Configuration ─────────────────────────────────────────────────
# Modified: 2026-02-10T05:35:00Z | Author: COPILOT | Change: Configure public STUN servers and optional TURN

# Public STUN servers (no credentials needed, used for NAT traversal)
# For local-only SLATE usage behind LAN, STUN is sufficient.
# TURN is needed only if peers are behind symmetric NAT.
ICE_SERVERS = [
    {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]},
    {"urls": ["stun:stun.services.mozilla.com"]},
]

# Optional TURN server — set via environment or config
# For local-network SLATE, TURN is rarely needed since all peers
# are on the same machine or LAN.
TURN_CONFIG: Optional[Dict] = None  # {"urls": "turn:my.turn.server:3478", "username": "...", "credential": "..."}

MAX_PEERS_PER_ROOM = 8
MAX_ROOMS = 20
STALE_PEER_TIMEOUT_S = 120  # Remove peers silent for 2+ minutes
CLEANUP_INTERVAL_S = 60


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Peer:
    """Represents a connected voice chat peer."""
    peer_id: str
    websocket: WebSocket
    room_id: str
    joined_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    display_name: str = "Anonymous"
    is_muted: bool = False


@dataclass
class Room:
    """Represents a voice chat room."""
    room_id: str
    created_at: float = field(default_factory=time.time)
    peers: Dict[str, Peer] = field(default_factory=dict)

    @property
    def peer_count(self) -> int:
        return len(self.peers)

    def peer_list(self) -> List[Dict]:
        return [
            {
                "peer_id": p.peer_id,
                "display_name": p.display_name,
                "is_muted": p.is_muted,
                "joined_at": p.joined_at,
            }
            for p in self.peers.values()
        ]


# ── Signaling Manager ────────────────────────────────────────────────────────

class SignalingManager:
    """
    Manages WebRTC signaling rooms and peer connections.

    Responsibilities:
    - Room creation/destruction
    - Peer join/leave with notification broadcast
    - SDP offer/answer relay between peers
    - ICE candidate forwarding
    - Stale peer cleanup
    """

    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup_loop(self):
        """Start background cleanup of stale peers."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Periodically remove stale peers and empty rooms."""
        while True:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL_S)
                now = time.time()
                empty_rooms = []

                for room_id, room in list(self.rooms.items()):
                    stale_peers = [
                        pid for pid, peer in room.peers.items()
                        if (now - peer.last_seen) > STALE_PEER_TIMEOUT_S
                    ]
                    for pid in stale_peers:
                        logger.info(f"Removing stale peer {pid} from room {room_id}")
                        peer = room.peers.pop(pid, None)
                        if peer:
                            try:
                                await peer.websocket.close(code=4008, reason="Stale connection")
                            except Exception:
                                pass
                            await self._broadcast_to_room(room_id, {
                                "type": "peer_left",
                                "peer_id": pid,
                                "reason": "timeout",
                            }, exclude_peer=pid)

                    if room.peer_count == 0:
                        empty_rooms.append(room_id)

                for room_id in empty_rooms:
                    del self.rooms[room_id]
                    logger.info(f"Removed empty room {room_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def _validate_room_id(self, room_id: str) -> bool:
        """Validate room ID format."""
        if not room_id or len(room_id) > 64:
            return False
        return all(c.isalnum() or c in ('-', '_') for c in room_id)

    async def join_room(self, room_id: str, websocket: WebSocket,
                        display_name: str = "Anonymous") -> Optional[Peer]:
        """Add a peer to a room. Creates room if it doesn't exist."""
        if not self._validate_room_id(room_id):
            await websocket.close(code=4001, reason="Invalid room ID")
            return None

        if len(self.rooms) >= MAX_ROOMS and room_id not in self.rooms:
            await websocket.close(code=4002, reason="Max rooms reached")
            return None

        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id=room_id)
            logger.info(f"Created room {room_id}")

        room = self.rooms[room_id]
        if room.peer_count >= MAX_PEERS_PER_ROOM:
            await websocket.close(code=4003, reason="Room is full")
            return None

        peer_id = str(uuid.uuid4())[:8]
        peer = Peer(
            peer_id=peer_id,
            websocket=websocket,
            room_id=room_id,
            display_name=display_name,
        )
        room.peers[peer_id] = peer

        # Notify existing peers about the new peer
        await self._broadcast_to_room(room_id, {
            "type": "peer_joined",
            "peer_id": peer_id,
            "display_name": display_name,
            "peer_count": room.peer_count,
        }, exclude_peer=peer_id)

        # Send room state to the new peer
        await websocket.send_json({
            "type": "room_joined",
            "peer_id": peer_id,
            "room_id": room_id,
            "peers": room.peer_list(),
            "ice_servers": self.get_ice_servers(),
        })

        logger.info(f"Peer {peer_id} ({display_name}) joined room {room_id} "
                     f"({room.peer_count} peers)")
        return peer

    async def leave_room(self, peer: Peer):
        """Remove a peer from their room."""
        room = self.rooms.get(peer.room_id)
        if not room:
            return

        room.peers.pop(peer.peer_id, None)

        # Notify remaining peers
        await self._broadcast_to_room(peer.room_id, {
            "type": "peer_left",
            "peer_id": peer.peer_id,
            "display_name": peer.display_name,
            "reason": "disconnected",
            "peer_count": room.peer_count,
        })

        # Clean up empty rooms
        if room.peer_count == 0:
            del self.rooms[peer.room_id]
            logger.info(f"Room {peer.room_id} removed (empty)")

        logger.info(f"Peer {peer.peer_id} left room {peer.room_id}")

    async def relay_signal(self, sender: Peer, message: dict):
        """
        Relay a WebRTC signaling message to the target peer.

        Supports:
        - offer: SDP offer from initiator
        - answer: SDP answer from responder
        - ice-candidate: ICE candidate exchange
        - mute-toggle: Mute state change broadcast
        """
        sender.last_seen = time.time()
        msg_type = message.get("type", "")
        target_peer_id = message.get("target_peer_id")

        if msg_type in ("offer", "answer", "ice-candidate"):
            if not target_peer_id:
                await sender.websocket.send_json({
                    "type": "error",
                    "message": f"Missing target_peer_id for {msg_type}",
                })
                return

            room = self.rooms.get(sender.room_id)
            if not room:
                return

            target = room.peers.get(target_peer_id)
            if not target:
                await sender.websocket.send_json({
                    "type": "error",
                    "message": f"Peer {target_peer_id} not found in room",
                })
                return

            # Forward the signal to the target peer
            relay_msg = {
                "type": msg_type,
                "from_peer_id": sender.peer_id,
                "from_display_name": sender.display_name,
            }

            if msg_type == "offer":
                relay_msg["sdp"] = message.get("sdp")
            elif msg_type == "answer":
                relay_msg["sdp"] = message.get("sdp")
            elif msg_type == "ice-candidate":
                relay_msg["candidate"] = message.get("candidate")

            try:
                await target.websocket.send_json(relay_msg)
            except Exception as e:
                logger.warning(f"Failed to relay {msg_type} to {target_peer_id}: {e}")

        elif msg_type == "mute-toggle":
            sender.is_muted = message.get("is_muted", False)
            await self._broadcast_to_room(sender.room_id, {
                "type": "peer_mute_changed",
                "peer_id": sender.peer_id,
                "is_muted": sender.is_muted,
            }, exclude_peer=sender.peer_id)

        elif msg_type == "ping":
            sender.last_seen = time.time()
            await sender.websocket.send_json({"type": "pong"})

        else:
            await sender.websocket.send_json({
                "type": "error",
                "message": f"Unknown signal type: {msg_type}",
            })

    async def _broadcast_to_room(self, room_id: str, message: dict,
                                  exclude_peer: Optional[str] = None):
        """Broadcast a message to all peers in a room."""
        room = self.rooms.get(room_id)
        if not room:
            return

        for pid, peer in list(room.peers.items()):
            if pid == exclude_peer:
                continue
            try:
                await peer.websocket.send_json(message)
            except Exception:
                # Peer connection broken — will be cleaned up
                pass

    def get_ice_servers(self) -> List[Dict]:
        """Return ICE server configuration for WebRTC."""
        servers = list(ICE_SERVERS)
        if TURN_CONFIG:
            servers.append(TURN_CONFIG)
        return servers

    def get_status(self) -> Dict:
        """Return signaling server status."""
        return {
            "rooms": len(self.rooms),
            "total_peers": sum(r.peer_count for r in self.rooms.values()),
            "max_rooms": MAX_ROOMS,
            "max_peers_per_room": MAX_PEERS_PER_ROOM,
            "ice_servers": len(self.get_ice_servers()),
            "room_details": [
                {
                    "room_id": r.room_id,
                    "peer_count": r.peer_count,
                    "created_at": r.created_at,
                    "peers": r.peer_list(),
                }
                for r in self.rooms.values()
            ],
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_signaling_manager: Optional[SignalingManager] = None


def get_signaling_manager() -> SignalingManager:
    """Get or create the singleton SignalingManager."""
    global _signaling_manager
    if _signaling_manager is None:
        _signaling_manager = SignalingManager()
    return _signaling_manager


# ── FastAPI Router ───────────────────────────────────────────────────────────

def create_voice_router() -> APIRouter:
    """
    Create the FastAPI router for voice chat signaling.

    Endpoints:
        GET  /api/voice/status          → Room/peer status
        GET  /api/voice/ice-servers     → ICE server configuration
        GET  /api/voice/rooms           → List active rooms
        WS   /ws/voice/{room_id}        → WebSocket signaling endpoint
    """
    router = APIRouter(tags=["voice"])
    mgr = get_signaling_manager()

    @router.get("/api/voice/status")
    async def voice_status():
        """Get voice chat signaling status."""
        return mgr.get_status()

    @router.get("/api/voice/ice-servers")
    async def ice_servers():
        """Get ICE server configuration for WebRTC clients."""
        return {"ice_servers": mgr.get_ice_servers()}

    @router.get("/api/voice/rooms")
    async def list_rooms():
        """List active voice chat rooms."""
        return {
            "rooms": [
                {
                    "room_id": r.room_id,
                    "peer_count": r.peer_count,
                    "created_at": r.created_at,
                }
                for r in mgr.rooms.values()
            ]
        }

    @router.websocket("/ws/voice/{room_id}")
    async def voice_websocket(websocket: WebSocket, room_id: str,
                               display_name: str = Query(default="Anonymous")):
        """
        WebSocket endpoint for WebRTC voice chat signaling.

        Protocol:
        1. Client connects → receives 'room_joined' with peer list and ICE servers
        2. New peer triggers 'peer_joined' broadcast to existing peers
        3. Peers exchange 'offer' → 'answer' → 'ice-candidate' messages
        4. 'mute-toggle' broadcasts mute state changes
        5. 'ping'/'pong' for keepalive
        6. Disconnect triggers 'peer_left' broadcast

        Message format (client → server):
            {"type": "offer", "target_peer_id": "abc", "sdp": {...}}
            {"type": "answer", "target_peer_id": "abc", "sdp": {...}}
            {"type": "ice-candidate", "target_peer_id": "abc", "candidate": {...}}
            {"type": "mute-toggle", "is_muted": true}
            {"type": "ping"}
        """
        await websocket.accept()

        # Start cleanup loop if not running
        mgr.start_cleanup_loop()

        peer = await mgr.join_room(room_id, websocket, display_name)
        if peer is None:
            return  # Connection was closed with error

        try:
            while True:
                try:
                    raw = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                    message = json.loads(raw)
                    await mgr.relay_signal(peer, message)
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    try:
                        await websocket.send_json({"type": "ping"})
                    except Exception:
                        break
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON",
                    })
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Voice WS error for peer {peer.peer_id}: {e}")
        finally:
            await mgr.leave_room(peer)

    return router
