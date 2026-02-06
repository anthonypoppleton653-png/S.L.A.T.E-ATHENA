<p align="center">
  <img src="docs/assets/slate-logo.svg" alt="SLATE Logo" width="200" height="200">
</p>

<h1 align="center">S.L.A.T.E.</h1>

<p align="center">
  <strong>Synchronized Living Architecture for Transformation and Evolution</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./actions"><img src="https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./wiki"><img src="https://img.shields.io/badge/docs-wiki-blue.svg" alt="Documentation"></a>
</p>

<p align="center">
  A <strong>GitHub-centric</strong> development framework with GPU-accelerated<br>
  self-hosted runners for automated CI/CD workflows.
</p>

---

> **Note**: This project is experimental. Not suitable for production use.

## Overview

SLATE provides GPU-accelerated CI/CD through GitHub Actions with self-hosted runners:

```
GitHub Repository (S.L.A.T.E.)
         |
    +----+----+
    v         v
  Cloud     Self-Hosted
  Runner     Runner
             (2x RTX 5070 Ti)
         |
         v
   GPU Workloads
   (tests, builds)
```

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E..git
cd S.L.A.T.E.
python install_slate.py
```

### 2. Verify Installation

```bash
python slate/slate_sdk.py --verify
```

### 3. With Self-Hosted Runner

```bash
python install_slate.py --runner --runner-token YOUR_TOKEN
```

Get your runner token from: https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./settings/actions/runners

## Self-Hosted Runner

| Property | Value |
|----------|-------|
| **Name** | `slate-DESKTOP-R3UD82D` |
| **Labels** | `self-hosted`, `slate`, `gpu`, `windows`, `cuda`, `gpu-2`, `blackwell` |
| **Hardware** | 2x RTX 5070 Ti (Blackwell) |

### Runner Commands

```bash
# Check status
python slate/slate_runner_manager.py --status

# Start runner
python slate/slate_runner_manager.py --start

# Stop runner
python slate/slate_runner_manager.py --stop

# Install as Windows service
python slate/slate_runner_manager.py --install-service
```

## Project Structure

```
slate/                  # Core SLATE SDK modules
  slate_sdk.py          # Unified SDK (setup, status, verify)
  slate_status.py       # System status checker
  slate_runner_manager.py     # GitHub runner management
  slate_github_integration.py # GitHub API integration
agents/                 # Dashboard and API servers
tests/                  # Test suite
.github/
  workflows/            # GitHub Actions workflows
```

## CLI Reference

```bash
# SDK Status
python slate/slate_sdk.py --status

# System Status
python slate/slate_status.py --quick

# Run Tests
python -m pytest tests/ -v

# Start Dashboard
python agents/slate_dashboard_server.py
```

## System Requirements

- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **Python**: 3.11+
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: NVIDIA RTX series (for self-hosted runner)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Repository](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E.)
- [Wiki](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./wiki)
- [Issues](https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E./issues)

---

<p align="center">
  <strong>S.L.A.T.E.</strong> - Synchronized Living Architecture for Transformation and Evolution
</p>
