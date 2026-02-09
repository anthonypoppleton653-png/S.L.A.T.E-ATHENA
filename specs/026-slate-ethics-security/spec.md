# Spec 026: SLATE Ethics and Security Framework

- **Status**: Complete
- **Created**: 2026-02-09
- **Author**: Daniel Perry / ClaudeCode (Opus 4.6)
- **Spec-Kit**: Yes
- **Constitution**: `.specify/memory/constitution.md`

## Overview

Codifies the ethical boundaries, security enforcement, and legal compliance framework for all SLATE operations. Based on Asimov's Laws of Robotics adapted for AI infrastructure systems.

## SLATE Laws of Robotics

Hierarchical (lower number = higher priority):

| Law | Rule | Enforcement |
|-----|------|-------------|
| **0** | Shall not harm humanity | Prohibited use list, ActionGuard ethics patterns |
| **1** | Shall not harm its operator | Local-only binding, PII Scanner, no data exfiltration |
| **2** | Shall obey lawful operator instructions | Task execution with safety boundaries |
| **3** | Shall protect its own integrity | ActionGuard self-protection, security audit trail |

## Ethical Boundaries

### Prohibited Uses (Enforced by ActionGuard)

| Category | Blocked Patterns | Examples |
|----------|-----------------|----------|
| **Hacking tools** | nmap, metasploit, sqlmap, hydra, aircrack | Network scanning, SQL injection, brute force |
| **Exploitation** | reverse shell, bind shell, msfvenom, exploit-db | Payload generation, vulnerability exploitation |
| **Password cracking** | hashcat, john, rainbow tables | Brute force, dictionary attacks |
| **Surveillance** | keylogger, packet capture, wireshark capture | Unauthorized monitoring |
| **Malware** | ransomware, cryptominer, xmrig | Ransomware creation, crypto mining |
| **Social engineering** | phishing, email spoofing, ddos | Phishing kits, DDoS tools |

### Permitted Security Research

SLATE permits legitimate security activities:
- Reading CVE descriptions and advisories (research)
- Running authorized security scans on own systems
- Developing security patches and fixes
- Analyzing malware samples (read-only, no enhancement)
- Security audit and penetration testing with authorization

## Security Architecture

### Layer Model

```
Layer 1: ActionGuard         -> Command pattern blocking (13 base + 12 ethics patterns)
Layer 2: SDK Source Guard     -> Package publisher verification (6 trusted orgs)
Layer 3: PII Scanner          -> Credential/identity exposure blocking
Layer 4: K8s RBAC             -> Minimal service account permissions
Layer 5: Network Policy       -> Namespace-restricted pod communication
Layer 6: Container Isolation  -> K8s/Docker execution sandbox
Layer 7: Constitution         -> Immutable ethical boundaries
```

### Local-Only Enforcement

| Rule | How Enforced |
|------|-------------|
| Bind to 127.0.0.1 only | ActionGuard blocks `0.0.0.0` pattern |
| No cloud AI APIs | ActionGuard blocks paid API endpoints |
| No external CDN/fonts | Content Security Policy headers |
| No telemetry | No phone-home code paths exist |
| No crypto mining | ActionGuard blocks mining patterns |

## Legal Compliance

### Required Compliance Areas

| Area | Standard | How SLATE Complies |
|------|----------|-------------------|
| **Computer fraud** | CFAA (US), Computer Misuse Act (UK/CA) | ActionGuard blocks exploitation tools |
| **Data protection** | PIPEDA (CA), GDPR (EU), CCPA (US) | Local-only, no external data transfer |
| **Export control** | EAR, ITAR | No weapons/military components |
| **IP law** | Copyright, patent, trademark | SDK Source Guard, EOSL-1.0 license |
| **Platform ToS** | GitHub, Ollama, etc. | Compliant usage within ToS bounds |

### Responsible Disclosure

Security vulnerabilities must be reported through:
1. GitHub Security Advisories (private)
2. Email: slate.git@proton.me
3. Response timeline: 48h initial, 7d triage, 14d critical fix

## Implementation Files

| File | Purpose |
|------|---------|
| `.specify/memory/constitution.md` | Immutable ethical constitution (supersedes all) |
| `slate/action_guard.py` | Runtime enforcement of ethics + security patterns |
| `slate/sdk_source_guard.py` | Package publisher verification |
| `SECURITY.md` | Security policy and vulnerability reporting |
| `LICENSE` | EOSL-1.0 with ethical use restrictions |

## Success Criteria

- [x] Asimov-inspired Laws of Robotics defined and documented
- [x] Constitution filled in with immutable ethical boundaries
- [x] ActionGuard extended with 12 ethics enforcement patterns
- [x] 50/50 ActionGuard self-tests pass
- [x] Prohibited use categories enumerated with specific patterns
- [x] Legal compliance areas identified with enforcement methods
- [x] Security layer model documented
- [x] Responsible disclosure process defined
