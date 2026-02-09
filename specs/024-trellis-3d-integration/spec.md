# Spec 024: TRELLIS.2 3D Generation Integration

- **Status**: Specified
- **Created**: 2026-02-09
- **Author**: ClaudeCode (Opus 4.6)
- **Spec-Kit**: Yes

## Overview

Integrate Microsoft TRELLIS.2 (4B parameter image-to-3D model) into SLATE as a containerized microservice for generating 3D assets from 2D images. Primary use case: SLATE avatar generation and system visualization.

## TRELLIS.2 Analysis

### Capabilities

- **Input**: Single 2D image (PNG/JPEG)
- **Output**: Textured 3D mesh (GLB with PBR materials: base color, roughness, metallic, opacity)
- **Architecture**: 3-stage DiT pipeline (Structure Flow → Shape Flow → Texture Flow)
- **Model Size**: 4B parameters total
- **Resolution**: 512^3 to 1536^3 voxels
- **Speed**: ~3s at 512^3 on H100

### Repository

| Field | Value |
|-------|-------|
| **Upstream** | microsoft/TRELLIS.2 |
| **Fork** | SynchronizedLivingArchitecture/TRELLIS.2 |
| **License** | MIT (core), NVIDIA Non-Commercial (nvdiffrast, nvdiffrec) |
| **Stars** | 3,537 |
| **Language** | Python |

### Hardware Constraints for SLATE

| Concern | Status | Mitigation |
|---------|--------|------------|
| VRAM (24GB minimum) | RTX 5070 Ti = 16GB | Use `low_vram` mode, target 512^3 |
| Blackwell (sm_120) | Active issues (#99, #102) | Monitor upstream, use spconv fallback |
| OS (Linux only) | SLATE on Windows | Deploy in K8s Linux container |
| NVIDIA license | nvdiffrast non-commercial | Internal/research use acceptable |

### Dependencies to Add

| Package | Purpose | License |
|---------|---------|---------|
| trimesh | 3D mesh handling | MIT |
| flash-attn | Fast attention | BSD |
| FlexGEMM | Sparse convolution | MIT |
| CuMesh | CUDA mesh processing | MIT |
| nvdiffrast | Differentiable rendering | NVIDIA Non-Commercial |
| kornia | Differentiable CV | Apache 2.0 |

## Integration Architecture

```
┌──────────────────────────────────────────────────────────┐
│                 SLATE Unified AI Backend                   │
│  unified_ai_backend.py                                    │
│  Task Type: 3d_generation → trellis2_service              │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│              TRELLIS.2 K8s Service                        │
│  trellis2-svc:8086                                       │
│                                                          │
│  Endpoints:                                              │
│    POST /generate    - Image to 3D mesh                  │
│    GET  /status      - Service health                    │
│    GET  /models      - Available model configs           │
│    GET  /assets/:id  - Retrieve generated assets         │
└──────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Fork and Container
1. Fork microsoft/TRELLIS.2 to SynchronizedLivingArchitecture
2. Build Docker image with CUDA 12.4 + all native extensions
3. Create K8s deployment manifest
4. Test basic image-to-3D pipeline

### Phase 2: API Service
1. Wrap TRELLIS.2 pipeline in FastAPI service
2. Add endpoints: /generate, /status, /models, /assets
3. Implement asset storage (persistent volume)
4. Connect to unified_ai_backend.py as new provider

### Phase 3: Avatar Pipeline
1. Generate SLATE avatar reference images (2D concept art)
2. Process through TRELLIS.2 pipeline
3. Post-process GLB for web delivery
4. Integrate model-viewer in dashboard and GitHub Pages

## K8s Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trellis2-generator
  namespace: slate
  labels:
    app: trellis2
    component: 3d-generation
spec:
  replicas: 1
  selector:
    matchLabels:
      app: trellis2
  template:
    metadata:
      labels:
        app: trellis2
    spec:
      containers:
      - name: trellis2
        image: ghcr.io/synchronizedlivingarchitecture/trellis2:latest
        resources:
          requests:
            memory: "8Gi"
            nvidia.com/gpu: 1
          limits:
            memory: "16Gi"
            nvidia.com/gpu: 1
        ports:
        - containerPort: 8086
          name: http
        env:
        - name: TRELLIS_LOW_VRAM
          value: "true"
        - name: TRELLIS_RESOLUTION
          value: "512"
        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache/huggingface
        - name: asset-storage
          mountPath: /app/assets
      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: trellis2-model-cache
      - name: asset-storage
        persistentVolumeClaim:
          claimName: trellis2-assets
---
apiVersion: v1
kind: Service
metadata:
  name: trellis2-svc
  namespace: slate
spec:
  selector:
    app: trellis2
  ports:
  - port: 8086
    targetPort: 8086
    name: http
```

## New Microsoft Dependencies (Research Results)

Based on comprehensive analysis, these high-priority Microsoft repos should be forked:

| Repository | Purpose | Priority |
|-----------|---------|----------|
| microsoft/graphrag | Knowledge graph RAG (upgrade ChromaDB) | HIGH |
| microsoft/Olive | Model quantization/optimization for dual GPU | HIGH |
| microsoft/agent-framework | Unified successor to semantic-kernel + autogen | HIGH |
| microsoft/presidio | NLP-powered PII detection upgrade | HIGH |
| microsoft/playwright-mcp | Browser automation via MCP | HIGH |
| microsoft/LLMLingua | 20x prompt compression for VRAM constraint | HIGH |
| microsoft/markitdown | Document-to-Markdown for RAG ingestion | MEDIUM |
| microsoft/devskim | Security linting for Python/JS | MEDIUM |
| microsoft/promptflow | Visual LLM workflow debugging | MEDIUM |

## Files

| File | Purpose |
|------|---------|
| `slate/slate_trellis.py` | TRELLIS.2 client and pipeline manager |
| `k8s/trellis2-generator.yaml` | K8s deployment manifest |
| `Dockerfile.trellis2` | Container image build |
| `.slate_identity/avatar_assets/` | Generated 3D assets |

## Success Criteria

- TRELLIS.2 fork created and synced
- Container builds successfully with all CUDA extensions
- K8s service responds on port 8086
- Can generate 512^3 GLB mesh from input image
- Integrated into unified_ai_backend.py as 3d_generation provider
- Generated avatar viewable via model-viewer
