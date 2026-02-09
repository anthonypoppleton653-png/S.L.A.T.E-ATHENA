#!/usr/bin/env python3
# Modified: 2026-02-09T22:30:00Z | Author: ClaudeCode (Opus 4.6) | Change: Initial TRELLIS.2 client and pipeline manager
"""
SLATE TRELLIS.2 3D Generation Client
======================================
Client module for the TRELLIS.2 K8s microservice (Microsoft 4B image-to-3D model).

Provides:
- Service health monitoring and status
- Image-to-3D mesh generation requests
- Asset retrieval and caching
- Integration with unified_ai_backend.py
- CLI for testing and management

Service architecture:
    slate_trellis.py (client) --> trellis2-svc:8086 (K8s service)
                                    |
                                    v
                              TRELLIS.2 4B model
                              (CUDA 12.4, low_vram mode)

Usage:
    python slate/slate_trellis.py --status
    python slate/slate_trellis.py --generate IMAGE_PATH
    python slate/slate_trellis.py --assets
    python slate/slate_trellis.py --json
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Add workspace root to path
WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(WORKSPACE_ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger("slate.trellis")

# ==============================================================================
# Configuration
# ==============================================================================

TRELLIS_HOST = os.environ.get("TRELLIS_HOST", "http://127.0.0.1:8086")
TRELLIS_K8S_SERVICE = "trellis2-svc.slate.svc.cluster.local:8086"
TRELLIS_TIMEOUT = int(os.environ.get("TRELLIS_TIMEOUT", "120"))  # 3D gen can be slow

# Asset storage
ASSET_DIR = WORKSPACE_ROOT / ".slate_identity" / "avatar_assets"
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# Model configuration
DEFAULT_CONFIG = {
    "resolution": 512,          # 512^3 voxels (low_vram mode)
    "low_vram": True,           # Required for 16GB RTX 5070 Ti
    "output_format": "glb",     # GLB with PBR materials
    "seed": 42,                 # Deterministic generation
    "texture_resolution": 1024, # Texture map resolution
    "remesh": True,             # Post-process mesh for web delivery
    "target_faces": 50000,      # Face budget for web-friendly mesh
}

# Supported input formats
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


# ==============================================================================
# Data Classes
# ==============================================================================

@dataclass
class TrellisServiceStatus:
    """Status of the TRELLIS.2 K8s service."""
    available: bool = False
    endpoint: str = TRELLIS_HOST
    version: str = ""
    gpu_name: str = ""
    gpu_memory_mb: int = 0
    model_loaded: bool = False
    low_vram_mode: bool = True
    resolution: int = 512
    uptime_seconds: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "endpoint": self.endpoint,
            "version": self.version,
            "gpu": {
                "name": self.gpu_name,
                "memory_mb": self.gpu_memory_mb,
            },
            "model_loaded": self.model_loaded,
            "low_vram_mode": self.low_vram_mode,
            "resolution": self.resolution,
            "uptime_seconds": self.uptime_seconds,
            "error": self.error,
        }


@dataclass
class GenerationRequest:
    """Request to generate a 3D mesh from a 2D image."""
    image_path: str
    resolution: int = 512
    output_format: str = "glb"
    seed: int = 42
    low_vram: bool = True
    texture_resolution: int = 1024
    remesh: bool = True
    target_faces: int = 50000

    def validate(self) -> tuple[bool, str]:
        """Validate the generation request."""
        path = Path(self.image_path)
        if not path.exists():
            return False, f"Image not found: {self.image_path}"
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            return False, f"Unsupported format: {path.suffix} (supported: {SUPPORTED_FORMATS})"
        if self.resolution not in (512, 768, 1024, 1536):
            return False, f"Invalid resolution: {self.resolution} (supported: 512, 768, 1024, 1536)"
        if self.resolution > 512 and self.low_vram:
            return False, f"Resolution {self.resolution} requires low_vram=false (>16GB VRAM)"
        return True, ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolution": self.resolution,
            "output_format": self.output_format,
            "seed": self.seed,
            "low_vram": self.low_vram,
            "texture_resolution": self.texture_resolution,
            "remesh": self.remesh,
            "target_faces": self.target_faces,
        }


@dataclass
class GenerationResult:
    """Result from a 3D generation request."""
    success: bool = False
    asset_id: str = ""
    output_path: str = ""
    format: str = "glb"
    vertices: int = 0
    faces: int = 0
    file_size_bytes: int = 0
    generation_time_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "asset_id": self.asset_id,
            "output_path": self.output_path,
            "format": self.format,
            "mesh": {
                "vertices": self.vertices,
                "faces": self.faces,
            },
            "file_size_bytes": self.file_size_bytes,
            "generation_time_ms": self.generation_time_ms,
            "error": self.error,
        }


@dataclass
class AssetInfo:
    """Information about a stored 3D asset."""
    asset_id: str
    filename: str
    format: str
    file_size_bytes: int
    created: str
    source_image: str = ""
    vertices: int = 0
    faces: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "filename": self.filename,
            "format": self.format,
            "file_size_bytes": self.file_size_bytes,
            "created": self.created,
            "source_image": self.source_image,
            "mesh": {
                "vertices": self.vertices,
                "faces": self.faces,
            },
        }


# ==============================================================================
# TRELLIS.2 Client
# ==============================================================================

class TrellisClient:
    """Client for the TRELLIS.2 K8s microservice."""

    def __init__(self, host: Optional[str] = None):
        self.host = (host or TRELLIS_HOST).rstrip("/")
        self.asset_dir = ASSET_DIR
        self._asset_manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, Any]:
        """Load the asset manifest."""
        manifest_path = self.asset_dir / "manifest.json"
        if manifest_path.exists():
            try:
                return json.loads(manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"assets": [], "generated_count": 0, "last_updated": ""}

    def _save_manifest(self) -> None:
        """Save the asset manifest."""
        self._asset_manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
        manifest_path = self.asset_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(self._asset_manifest, indent=2),
            encoding="utf-8",
        )

    def _api_request(
        self,
        path: str,
        method: str = "GET",
        data: Optional[bytes] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: int = TRELLIS_TIMEOUT,
    ) -> tuple[bool, Any]:
        """Make an API request to the TRELLIS.2 service."""
        url = f"{self.host}{path}"
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)

        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers=req_headers,
                method=method,
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                if resp.headers.get("Content-Type", "").startswith("application/json"):
                    return True, json.loads(body)
                return True, body
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            return False, f"HTTP {e.code}: {error_body or e.reason}"
        except urllib.error.URLError as e:
            return False, f"Connection failed: {e.reason}"
        except TimeoutError:
            return False, f"Request timed out after {timeout}s"
        except Exception as e:
            return False, f"Request error: {e}"

    # ──────────────────────────────────────────────────────────────────────────
    # Service Health
    # ──────────────────────────────────────────────────────────────────────────

    def get_status(self) -> TrellisServiceStatus:
        """Check the TRELLIS.2 service status."""
        status = TrellisServiceStatus(endpoint=self.host)

        ok, data = self._api_request("/status", timeout=10)
        if not ok:
            status.error = str(data)
            return status

        if isinstance(data, dict):
            status.available = True
            status.version = data.get("version", "unknown")
            status.gpu_name = data.get("gpu", {}).get("name", "")
            status.gpu_memory_mb = data.get("gpu", {}).get("memory_mb", 0)
            status.model_loaded = data.get("model_loaded", False)
            status.low_vram_mode = data.get("low_vram", True)
            status.resolution = data.get("resolution", 512)
            status.uptime_seconds = data.get("uptime_seconds", 0.0)

        return status

    def is_available(self) -> bool:
        """Quick check if the service is reachable."""
        try:
            req = urllib.request.Request(f"{self.host}/status", method="GET")
            with urllib.request.urlopen(req, timeout=5):
                return True
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # 3D Generation
    # ──────────────────────────────────────────────────────────────────────────

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a 3D mesh from a 2D image."""
        # Validate request
        valid, error = request.validate()
        if not valid:
            return GenerationResult(success=False, error=error)

        # Check service availability
        if not self.is_available():
            return GenerationResult(
                success=False,
                error=f"TRELLIS.2 service not available at {self.host}",
            )

        # Read image file
        image_path = Path(request.image_path)
        image_data = image_path.read_bytes()

        # Build multipart form data
        import uuid
        boundary = f"----SLATEBoundary{uuid.uuid4().hex[:16]}"
        body = b""

        # Add image file
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"\r\n'.encode()
        body += f"Content-Type: image/{image_path.suffix.lstrip('.').replace('jpg', 'jpeg')}\r\n\r\n".encode()
        body += image_data
        body += b"\r\n"

        # Add config as JSON field
        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="config"\r\n'
        body += b"Content-Type: application/json\r\n\r\n"
        body += json.dumps(request.to_dict()).encode()
        body += b"\r\n"

        body += f"--{boundary}--\r\n".encode()

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }

        start = time.monotonic()
        ok, data = self._api_request(
            "/generate",
            method="POST",
            data=body,
            headers=headers,
            timeout=TRELLIS_TIMEOUT,
        )
        elapsed_ms = (time.monotonic() - start) * 1000

        if not ok:
            return GenerationResult(
                success=False,
                error=str(data),
                generation_time_ms=elapsed_ms,
            )

        # Handle JSON response (asset metadata)
        if isinstance(data, dict):
            asset_id = data.get("asset_id", "")
            # Download the generated asset
            if asset_id:
                return self._download_asset(asset_id, elapsed_ms, image_path.name)
            return GenerationResult(
                success=False,
                error="No asset_id in response",
                generation_time_ms=elapsed_ms,
            )

        # Handle binary response (direct GLB)
        if isinstance(data, bytes):
            asset_id = f"trellis_{int(time.time())}_{image_path.stem}"
            output_path = self.asset_dir / f"{asset_id}.glb"
            output_path.write_bytes(data)

            result = GenerationResult(
                success=True,
                asset_id=asset_id,
                output_path=str(output_path),
                format="glb",
                file_size_bytes=len(data),
                generation_time_ms=elapsed_ms,
            )

            # Update manifest
            self._asset_manifest["assets"].append({
                "asset_id": asset_id,
                "filename": f"{asset_id}.glb",
                "source_image": image_path.name,
                "created": datetime.now(timezone.utc).isoformat(),
                "file_size_bytes": len(data),
            })
            self._asset_manifest["generated_count"] += 1
            self._save_manifest()

            return result

        return GenerationResult(
            success=False,
            error="Unexpected response format",
            generation_time_ms=elapsed_ms,
        )

    def _download_asset(
        self, asset_id: str, elapsed_ms: float, source_image: str = ""
    ) -> GenerationResult:
        """Download a generated asset by ID."""
        ok, data = self._api_request(f"/assets/{asset_id}", timeout=60)
        if not ok:
            return GenerationResult(
                success=False,
                asset_id=asset_id,
                error=f"Failed to download asset: {data}",
                generation_time_ms=elapsed_ms,
            )

        if isinstance(data, bytes):
            output_path = self.asset_dir / f"{asset_id}.glb"
            output_path.write_bytes(data)

            result = GenerationResult(
                success=True,
                asset_id=asset_id,
                output_path=str(output_path),
                format="glb",
                file_size_bytes=len(data),
                generation_time_ms=elapsed_ms,
            )

            # Update manifest
            self._asset_manifest["assets"].append({
                "asset_id": asset_id,
                "filename": f"{asset_id}.glb",
                "source_image": source_image,
                "created": datetime.now(timezone.utc).isoformat(),
                "file_size_bytes": len(data),
            })
            self._asset_manifest["generated_count"] += 1
            self._save_manifest()

            return result

        return GenerationResult(
            success=False,
            asset_id=asset_id,
            error="Asset download returned non-binary data",
            generation_time_ms=elapsed_ms,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Asset Management
    # ──────────────────────────────────────────────────────────────────────────

    def list_assets(self) -> list[AssetInfo]:
        """List all locally cached 3D assets."""
        assets = []
        for entry in self._asset_manifest.get("assets", []):
            filepath = self.asset_dir / entry.get("filename", "")
            if filepath.exists():
                assets.append(AssetInfo(
                    asset_id=entry.get("asset_id", ""),
                    filename=entry.get("filename", ""),
                    format=entry.get("filename", "").rsplit(".", 1)[-1] if "." in entry.get("filename", "") else "unknown",
                    file_size_bytes=filepath.stat().st_size,
                    created=entry.get("created", ""),
                    source_image=entry.get("source_image", ""),
                    vertices=entry.get("vertices", 0),
                    faces=entry.get("faces", 0),
                ))
        return assets

    def get_asset_path(self, asset_id: str) -> Optional[Path]:
        """Get the local file path for an asset."""
        for entry in self._asset_manifest.get("assets", []):
            if entry.get("asset_id") == asset_id:
                filepath = self.asset_dir / entry.get("filename", "")
                if filepath.exists():
                    return filepath
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Models & Configuration
    # ──────────────────────────────────────────────────────────────────────────

    def get_models(self) -> list[dict[str, Any]]:
        """Get available model configurations from the service."""
        ok, data = self._api_request("/models", timeout=10)
        if ok and isinstance(data, dict):
            return data.get("models", [])
        return []

    def get_config(self) -> dict[str, Any]:
        """Get the default generation configuration."""
        return dict(DEFAULT_CONFIG)


# ==============================================================================
# Unified AI Backend Integration
# ==============================================================================

class TrellisProvider:
    """Provider adapter for unified_ai_backend.py integration.

    Registers as a '3d_generation' task type in the SLATE AI routing system.
    """

    PROVIDER_NAME = "trellis2"
    TASK_TYPES = ["3d_generation", "avatar_generation", "asset_generation"]

    def __init__(self, host: Optional[str] = None):
        self.client = TrellisClient(host)

    def is_available(self) -> bool:
        """Check if TRELLIS.2 service is reachable."""
        return self.client.is_available()

    def get_status(self) -> dict[str, Any]:
        """Get provider status for unified backend."""
        status = self.client.get_status()
        return {
            "name": self.PROVIDER_NAME,
            "available": status.available,
            "endpoint": status.endpoint,
            "gpu": status.gpu_name,
            "model_loaded": status.model_loaded,
            "resolution": status.resolution,
            "error": status.error,
        }

    def execute(self, task: str, **kwargs) -> dict[str, Any]:
        """Execute a 3D generation task.

        Args:
            task: Task description or image path
            **kwargs: Generation configuration overrides

        Returns:
            Result dict compatible with unified_ai_backend InferenceResult
        """
        image_path = kwargs.get("image_path", task)
        if not Path(image_path).exists():
            return {
                "success": False,
                "provider": self.PROVIDER_NAME,
                "error": f"Image not found: {image_path}",
            }

        request = GenerationRequest(
            image_path=image_path,
            resolution=kwargs.get("resolution", DEFAULT_CONFIG["resolution"]),
            output_format=kwargs.get("output_format", DEFAULT_CONFIG["output_format"]),
            seed=kwargs.get("seed", DEFAULT_CONFIG["seed"]),
            low_vram=kwargs.get("low_vram", DEFAULT_CONFIG["low_vram"]),
            texture_resolution=kwargs.get("texture_resolution", DEFAULT_CONFIG["texture_resolution"]),
            remesh=kwargs.get("remesh", DEFAULT_CONFIG["remesh"]),
            target_faces=kwargs.get("target_faces", DEFAULT_CONFIG["target_faces"]),
        )

        result = self.client.generate(request)
        return {
            "success": result.success,
            "provider": self.PROVIDER_NAME,
            "model": "trellis2-4b",
            "response": result.output_path if result.success else result.error,
            "asset_id": result.asset_id,
            "generation_time_ms": result.generation_time_ms,
            "cost": "FREE",
        }


# ==============================================================================
# CLI Output
# ==============================================================================

# ANSI colors matching SLATE brand
RUST = "\033[38;2;184;90;60m"
BLUE = "\033[38;2;13;27;42m"
TEAL = "\033[38;2;27;58;75m"
GREEN = "\033[38;2;0;230;118m"
AMBER = "\033[38;2;255;183;77m"
RED = "\033[38;2;244;67;54m"
WHITE = "\033[38;2;224;224;224m"
DIM = "\033[38;2;128;128;128m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _print_status(client: TrellisClient) -> None:
    """Print TRELLIS.2 service status."""
    status = client.get_status()

    print(f"\n{'=' * 60}")
    print(f"  {RUST}{BOLD}TRELLIS.2 3D Generation Service{RESET}")
    print(f"{'=' * 60}")

    avail_color = GREEN if status.available else RED
    avail_text = "Online" if status.available else "Offline"
    print(f"\n  {WHITE}Status:{RESET}     {avail_color}{avail_text}{RESET}")
    print(f"  {WHITE}Endpoint:{RESET}   {DIM}{status.endpoint}{RESET}")

    if status.available:
        print(f"  {WHITE}Version:{RESET}    {DIM}{status.version}{RESET}")
        print(f"  {WHITE}GPU:{RESET}        {DIM}{status.gpu_name} ({status.gpu_memory_mb}MB){RESET}")

        model_color = GREEN if status.model_loaded else AMBER
        model_text = "Loaded" if status.model_loaded else "Not loaded"
        print(f"  {WHITE}Model:{RESET}      {model_color}{model_text}{RESET}")
        print(f"  {WHITE}Low VRAM:{RESET}   {DIM}{'Yes' if status.low_vram_mode else 'No'}{RESET}")
        print(f"  {WHITE}Resolution:{RESET} {DIM}{status.resolution}^3 voxels{RESET}")
        print(f"  {WHITE}Uptime:{RESET}     {DIM}{status.uptime_seconds:.0f}s{RESET}")
    else:
        print(f"  {WHITE}Error:{RESET}      {RED}{status.error}{RESET}")
        print(f"\n  {DIM}The TRELLIS.2 service runs as a K8s microservice.")
        print(f"  Deploy with: kubectl apply -f k8s/trellis2-generator.yaml{RESET}")

    # Local assets
    assets = client.list_assets()
    print(f"\n  {WHITE}Local Assets:{RESET} {DIM}{len(assets)} cached{RESET}")
    for asset in assets[:5]:
        size_kb = asset.file_size_bytes / 1024
        print(f"    {DIM}- {asset.asset_id} ({size_kb:.1f}KB, {asset.format}){RESET}")
    if len(assets) > 5:
        print(f"    {DIM}... and {len(assets) - 5} more{RESET}")

    # Configuration
    config = client.get_config()
    print(f"\n  {WHITE}Default Config:{RESET}")
    print(f"    {DIM}Resolution:   {config['resolution']}^3 voxels{RESET}")
    print(f"    {DIM}Low VRAM:     {config['low_vram']}{RESET}")
    print(f"    {DIM}Format:       {config['output_format']}{RESET}")
    print(f"    {DIM}Texture:      {config['texture_resolution']}px{RESET}")
    print(f"    {DIM}Target faces: {config['target_faces']}{RESET}")

    print(f"\n{'=' * 60}")


def _print_json(client: TrellisClient) -> None:
    """Print status as JSON."""
    status = client.get_status()
    assets = client.list_assets()
    output = {
        "service": status.to_dict(),
        "assets": [a.to_dict() for a in assets],
        "config": client.get_config(),
        "provider": TrellisProvider(client.host).get_status(),
    }
    print(json.dumps(output, indent=2))


def _print_assets(client: TrellisClient) -> None:
    """Print local asset inventory."""
    assets = client.list_assets()

    print(f"\n{'=' * 60}")
    print(f"  {RUST}{BOLD}TRELLIS.2 Asset Inventory{RESET}")
    print(f"{'=' * 60}")

    if not assets:
        print(f"\n  {DIM}No assets generated yet.{RESET}")
        print(f"  {DIM}Generate with: python slate/slate_trellis.py --generate IMAGE_PATH{RESET}")
    else:
        total_size = sum(a.file_size_bytes for a in assets)
        print(f"\n  {WHITE}Total:{RESET} {DIM}{len(assets)} assets ({total_size / 1024:.1f}KB){RESET}")
        print()
        for asset in assets:
            size_kb = asset.file_size_bytes / 1024
            print(f"  {GREEN}*{RESET} {WHITE}{asset.asset_id}{RESET}")
            print(f"    {DIM}File: {asset.filename} ({size_kb:.1f}KB){RESET}")
            if asset.source_image:
                print(f"    {DIM}Source: {asset.source_image}{RESET}")
            if asset.vertices:
                print(f"    {DIM}Mesh: {asset.vertices} verts, {asset.faces} faces{RESET}")
            print(f"    {DIM}Created: {asset.created}{RESET}")

    print(f"\n  {WHITE}Storage:{RESET} {DIM}{client.asset_dir}{RESET}")
    print(f"\n{'=' * 60}")


# ==============================================================================
# Main
# ==============================================================================

def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="SLATE TRELLIS.2 3D Generation Client")
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--generate", type=str, metavar="IMAGE", help="Generate 3D mesh from image")
    parser.add_argument("--assets", action="store_true", help="List local assets")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--resolution", type=int, default=512, help="Voxel resolution (default: 512)")
    parser.add_argument("--host", type=str, default=None, help="Override service host")
    args = parser.parse_args()

    client = TrellisClient(host=args.host)

    if args.json:
        _print_json(client)
    elif args.generate:
        request = GenerationRequest(
            image_path=args.generate,
            resolution=args.resolution,
        )
        valid, error = request.validate()
        if not valid:
            print(f"  {RED}Error:{RESET} {error}")
            sys.exit(1)

        print(f"  {AMBER}Generating 3D mesh from {args.generate}...{RESET}")
        result = client.generate(request)
        if result.success:
            print(f"  {GREEN}Success!{RESET}")
            print(f"  Asset ID: {result.asset_id}")
            print(f"  Output:   {result.output_path}")
            print(f"  Size:     {result.file_size_bytes / 1024:.1f}KB")
            print(f"  Time:     {result.generation_time_ms:.0f}ms")
        else:
            print(f"  {RED}Failed:{RESET} {result.error}")
            sys.exit(1)
    elif args.assets:
        _print_assets(client)
    else:
        _print_status(client)


if __name__ == "__main__":
    main()
