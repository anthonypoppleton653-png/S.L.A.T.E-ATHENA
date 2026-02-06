#!/usr/bin/env python3
# Modified: 2026-02-06T21:00:00Z | Author: Claude | Change: Runner API for dashboard integration
"""
SLATE Runner API
=================
Provides HTTP endpoints for the SLATE Dashboard to control and monitor
the self-hosted GitHub Actions runner.

Endpoints:
    GET  /api/runner/status     → Current runner status JSON
    POST /api/runner/start      → Start runner (interactive or service)
    POST /api/runner/stop       → Stop runner service
    POST /api/runner/provision  → Provision SLATE environment
    GET  /api/runner/labels     → Get runner labels
    GET  /api/runner/gpu        → GPU detection info
    GET  /api/runner/events     → SSE stream of runner events
"""

import asyncio
import json
import os
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))


# ─── SSE Queue for async broadcasting ─────────────────────────────────────────
_event_queues: list = []
_queue_lock = threading.Lock()


def _broadcast_event(event_type: str, data: dict):
    """Broadcast an event to all connected SSE clients."""
    msg = json.dumps({"event": event_type, "data": data, "ts": datetime.now().isoformat()})
    with _queue_lock:
        dead = []
        for q in _event_queues:
            try:
                q.put_nowait(msg)
            except Exception:
                dead.append(q)
        for d in dead:
            _event_queues.remove(d)


# ─── API Route Registration ─────────────────────────────────────────────────────

def add_runner_endpoints(app):
    """Register runner API endpoints on a FastAPI app instance.

    Called by slate_dashboard_server.py to mount runner controls
    into the main dashboard.
    """
    from fastapi import BackgroundTasks, Request
    from fastapi.responses import JSONResponse, StreamingResponse

    @app.get("/api/runner/status")
    async def runner_status():
        """Return current runner status."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()
            status = manager.get_status()
            return JSONResponse(content=status)
        except Exception as e:
            return JSONResponse(content={
                "installed": False,
                "configured": False,
                "provisioned": False,
                "running": False,
                "error": str(e),
            }, status_code=500)

    @app.get("/api/runner/gpu")
    async def runner_gpu():
        """Return GPU detection info."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()
            gpu_info = manager.detect_gpu()
            return JSONResponse(content=gpu_info)
        except Exception as e:
            return JSONResponse(content={
                "has_gpu": False,
                "gpu_count": 0,
                "gpu_names": [],
                "error": str(e),
            })

    @app.get("/api/runner/labels")
    async def runner_labels():
        """Return runner labels."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()
            labels = manager.get_runner_labels()
            return JSONResponse(content={"labels": labels})
        except Exception as e:
            return JSONResponse(content={"labels": [], "error": str(e)})

    @app.post("/api/runner/start")
    async def runner_start(background_tasks: BackgroundTasks, as_service: bool = False):
        """Start the runner."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()

            def _start():
                result = manager.start_runner(as_service=as_service)
                _broadcast_event("runner_started" if result["success"] else "runner_error", result)

            # Run in background thread (start is blocking)
            background_tasks.add_task(_start)

            return JSONResponse(content={
                "success": True,
                "message": "Runner starting...",
                "as_service": as_service,
            })
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "error": str(e),
            }, status_code=500)

    @app.post("/api/runner/stop")
    async def runner_stop():
        """Stop the runner service."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()
            result = manager.stop_service()
            _broadcast_event("runner_stopped" if result["success"] else "runner_error", result)
            return JSONResponse(content=result)
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "error": str(e),
            }, status_code=500)

    @app.post("/api/runner/provision")
    async def runner_provision(background_tasks: BackgroundTasks):
        """Provision SLATE environment for the runner."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()

            def _provision():
                _broadcast_event("provision_started", {"status": "in_progress"})
                result = manager.provision_slate_environment()
                _broadcast_event("provision_complete" if result["success"] else "provision_error", result)

            background_tasks.add_task(_provision)

            return JSONResponse(content={
                "success": True,
                "message": "Provisioning started...",
            })
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "error": str(e),
            }, status_code=500)

    @app.post("/api/runner/create-startup")
    async def runner_create_startup():
        """Create startup scripts for auto-start."""
        try:
            from slate.slate_runner_manager import SlateRunnerManager
            manager = SlateRunnerManager()
            script_path = manager.create_startup_script()
            svc_result = manager.create_windows_service_config()
            return JSONResponse(content={
                "success": True,
                "startup_script": str(script_path),
                "service_config": svc_result,
            })
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "error": str(e),
            }, status_code=500)

    @app.get("/api/runner/events")
    async def runner_events(request: Request):
        """SSE endpoint — streams runner events in real-time."""
        q = queue.Queue(maxsize=200)
        with _queue_lock:
            _event_queues.append(q)

        async def event_generator():
            try:
                # Send initial status
                try:
                    from slate.slate_runner_manager import SlateRunnerManager
                    manager = SlateRunnerManager()
                    status = manager.get_status()
                    yield f"event: init\ndata: {json.dumps(status, default=str)}\n\n"
                except Exception:
                    yield f"event: init\ndata: {{}}\n\n"

                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        msg = q.get_nowait()
                        yield f"event: update\ndata: {msg}\n\n"
                    except queue.Empty:
                        # Send keepalive every 5s
                        yield f"event: ping\ndata: {{}}\n\n"
                        await asyncio.sleep(5)
            finally:
                with _queue_lock:
                    if q in _event_queues:
                        _event_queues.remove(q)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )


# ─── Standalone test server ─────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        from fastapi import FastAPI
        import uvicorn
    except ImportError:
        print("[ERROR] FastAPI/uvicorn not installed")
        sys.exit(1)

    app = FastAPI(title="SLATE Runner API")
    add_runner_endpoints(app)

    @app.get("/")
    async def root():
        return {"message": "SLATE Runner API", "endpoints": [
            "/api/runner/status",
            "/api/runner/gpu",
            "/api/runner/labels",
            "/api/runner/start",
            "/api/runner/stop",
            "/api/runner/provision",
            "/api/runner/events",
        ]}

    print("[SLATE] Starting Runner API on http://127.0.0.1:8081")
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")
