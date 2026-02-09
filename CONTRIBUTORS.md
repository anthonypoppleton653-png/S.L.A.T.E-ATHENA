# SLATE Contributors and Compensation Framework
<!-- Modified: 2026-02-09T23:00:00Z | Author: ClaudeCode (Opus 4.6) | Change: Initial contributor framework with fair compensation -->

## Creator

| Role | Name | Service | Contact |
|------|------|---------|---------|
| **Creator & Owner** | Daniel Perry | Canadian Forces Veteran, Afghanistan (TF 3-09, PPCLI) | slate.git@proton.me |

## AI Development Partners

S.L.A.T.E. is built through **vibe coding** -- human vision guided by AI implementation. The following AI systems have contributed to the codebase:

| Partner | Role | Contribution |
|---------|------|-------------|
| **Claude Code** (Opus 4.6) | Primary Implementation | Architecture, modules, specs, infrastructure |
| **GitHub Copilot** | Co-development | Code suggestions, test generation, autonomous loop |
| **Ollama** (Mistral-Nemo) | Local AI Operations | Autonomous maintenance, classification, planning |

## How Contributor Compensation Works

SLATE uses the **EOSL-1.0 license** which includes a fair compensation framework. When commercial use of SLATE generates significant revenue ($1M+ USD annually), royalties are calculated using a **progressive formula** (like tax brackets -- only revenue within each band is charged at that band's rate):

| Revenue Band | Rate | Applied To |
|-------------|------|-----------|
| First $1M | 0% (free) | $0 - $1,000,000 |
| $1M - $5M | 2% | Next $4,000,000 |
| $5M - $25M | 3% | Next $20,000,000 |
| Above $25M | 5% | Remaining revenue |

25% of all royalties flow to the **Contributor Compensation Pool**.

### Revenue Distribution

```
Commercial Royalties (from EOSL-1.0 Section 1.2)
    |
    +-- 60% --> Creator (Daniel Perry)
    |
    +-- 25% --> Contributor Compensation Pool
    |               |
    |               +-- Distributed by objective contribution metrics
    |               +-- Recalculated quarterly
    |               +-- Paid annually
    |
    +-- 15% --> Project Infrastructure
                    |
                    +-- Hardware expansion (GPUs, DGX, compute)
                    +-- CI/CD and hosting costs
                    +-- Security auditing
```

### Contribution Scoring

Contributor shares are calculated using objective, automated metrics drawn from git history and GitHub API data:

| Metric | Weight | How It's Measured |
|--------|--------|-------------------|
| **Productive Code** | 25% | Net non-trivial LOC added/modified (excludes auto-generated, whitespace, comments-only) |
| **Test Coverage** | 20% | Coverage percentage delta from contributor's merged PRs |
| **Issue Resolution** | 15% | Count of issues closed via merged PRs (`Closes #N` / `Fixes #N`) |
| **Code Review** | 15% | Number of substantive reviews provided on others' PRs |
| **Documentation** | 10% | Docs, specs, wiki pages, README improvements |
| **Security** | 10% | Vulnerability reports, security fixes, ActionGuard improvements |
| **Community** | 5% | Discussion answers (Galaxy Brain), mentoring, support |

### Measurement Tools

SLATE provides built-in tools for transparent contribution analysis:

```powershell
# Analyze contributor metrics (reads git history + GitHub API)
python slate/slate_fork_sync.py --analyze

# View GitHub achievement progress
python slate/github_achievements.py --status

# Check fork quality tiers
python slate/slate_fork_sync.py --status
```

### Fork Maintainer Tiers

Established fork maintainers who create high-quality forks with original enhancements receive multiplied shares:

| Tier | Criteria | Share Multiplier |
|------|----------|-----------------|
| **Gold** | 50+ stars, active maintenance, original features, passing CI | 2.0x |
| **Silver** | 20+ stars, regular updates, useful modifications | 1.5x |
| **Bronze** | Active maintenance (commits within 30 days), meaningful contributions | 1.0x |

Fork quality is assessed quarterly using automated analysis.

### Qualifying for Compensation

To receive compensation from the Contributor Pool, you must:

1. **Have merged PRs** in the official SLATE repository, OR
2. **Maintain an established fork** with original enhancements (not trivial forks)
3. **Sign the Contributor Agreement** (included in your first PR via the PR template)
4. **Provide payment details** when notified of a distribution (handled privately)

### Transparency

- Contribution scores are calculated using publicly auditable git data
- Score methodology is open source (this document + SLATE analysis tools)
- Quarterly reports will be published in GitHub Discussions when royalties are active
- Any contributor may request a detailed breakdown of their score

## Hardware Donors

The SLATE project accepts hardware donations to expand local AI processing capabilities. Donors are recognized here.

| Donor | Contribution | Date |
|-------|-------------|------|
| *Accepting donations* | DGX units, GPUs, compute hardware | - |

**Contact for hardware donations**: slate.git@proton.me

### What We Need

| Priority | Hardware | Purpose |
|----------|----------|---------|
| **HIGH** | NVIDIA DGX or A100/H100 GPUs | Expand local inference beyond dual RTX 5070 Ti |
| **HIGH** | Enterprise NVMe storage (4TB+) | Model cache and training data |
| **MEDIUM** | Additional RTX 5090/5080 GPUs | Multi-GPU inference scaling |
| **MEDIUM** | High-bandwidth networking (25GbE+) | K8s cluster interconnect |
| **LOW** | Cloud compute credits | CI/CD pipeline (NOT for production inference) |

### Donor Benefits

| Tier | Donation Value | Benefits |
|------|---------------|----------|
| **Platinum** | $10,000+ or DGX system | Named recognition, priority features, direct communication channel |
| **Gold** | $5,000+ or enterprise GPU | Named recognition, priority feature requests |
| **Silver** | $1,000+ or consumer GPU | Named recognition in CONTRIBUTORS.md |
| **Bronze** | Any hardware contribution | Recognition in CONTRIBUTORS.md |

## Current Contributors

*This section will be populated as external contributors join the project.*

### How to Become a Contributor

1. **Fork** the repository: https://github.com/SynchronizedLivingArchitecture/S.L.A.T.E
2. Read the [CONTRIBUTING.md](CONTRIBUTING.md) guidelines
3. Create a feature branch and make your changes
4. Submit a Pull Request
5. Your PR will be reviewed and, if accepted, you become a recognized contributor

### GitHub Achievement Goals

SLATE development practices are designed to help contributors earn GitHub Achievements:

| Achievement | How SLATE Helps | Target Tier |
|-------------|----------------|-------------|
| **Pull Shark** | PR-based workflow, small focused changes | Gold (1,024 merged PRs) |
| **Pair Extraordinaire** | Co-authored commits with AI partners | Gold (48 co-authored PRs) |
| **Galaxy Brain** | Active GitHub Discussions Q&A | Gold (32 accepted answers) |
| **Starstruck** | Quality open-source project | Bronze+ (128+ stars) |
| **Quickdraw** | Rapid issue triage workflow | Default |
| **YOLO** | Solo maintainer fast-merge for trivial fixes | Default |

Track your progress: `python slate/github_achievements.py --refresh`

---

*This framework is governed by the [EOSL-1.0 License](LICENSE). All compensation provisions are legally binding once commercial revenue thresholds are met.*
