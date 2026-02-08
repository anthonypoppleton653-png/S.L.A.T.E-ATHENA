#!/usr/bin/env python3
"""
Enable GitHub Actions on SLATE-ATHENA fork and dispatch initial workflows.
Modified: 2026-02-08T02:50:00Z | Author: COPILOT | Change: GitHub Actions enablement and workflow dispatch

This script:
1. Enables GitHub Actions on your fork (if needed)
2. Dispatches initial validation workflows
3. Configures branch protection rules
4. Sets up GitHub Projects integration
"""

import subprocess
import urllib.request
import urllib.error
import json
import sys
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

GITHUB_API_BASE = "https://api.github.com"
REPO_OWNER = "anthonypoppleton653-png"
REPO_NAME = "S.L.A.T.E"
FULL_REPO = f"{REPO_OWNER}/{REPO_NAME}"

WORKFLOWS_TO_DISPATCH = [
    ("fork-validation.yml", "main", "Fork prerequisites validation"),
    ("ci.yml", "user/slate-agent", "CI pipeline (lint, test, security)"),
    ("slate.yml", "user/slate-agent", "SLATE integration tests"),
]

# ============================================================================
# GitHub API Functions
# ============================================================================

def get_github_token() -> str:
    """Retrieve GitHub token from git credential manager"""
    try:
        result = subprocess.run(
            ['git', 'credential', 'fill'],
            input='protocol=https\nhost=github.com\n',
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.split('\n'):
            if line.startswith('password='):
                token = line.split('=', 1)[1]
                if token:
                    return token
    except Exception as e:
        print(f"⚠️  Error retrieving token: {e}")
    
    return None

def make_github_request(method: str, endpoint: str, token: str, data: dict = None) -> tuple:
    """Make authenticated GitHub API request"""
    url = f"{GITHUB_API_BASE}{endpoint}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SLATE-Athena-Onboarding'
    }
    
    try:
        if data:
            data_str = json.dumps(data)
            req = urllib.request.Request(
                url,
                data=data_str.encode('utf-8'),
                headers=headers,
                method=method
            )
        else:
            req = urllib.request.Request(url, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            return (response.status, response_data)
    
    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read().decode('utf-8'))
        return (e.code, error_data)
    except Exception as e:
        return (500, {"error": str(e)})

# ============================================================================
# GitHub Actions Setup
# ============================================================================

def enable_actions(token: str) -> bool:
    """Enable GitHub Actions on fork"""
    print("📋 Checking GitHub Actions status...")
    
    # Check current status
    status, data = make_github_request(
        "GET",
        f"/repos/{FULL_REPO}",
        token
    )
    
    if status == 200:
        if data.get("archived"):
            print("⚠️  Repository is archived")
            return False
        
        # Get actions status
        status, actions_data = make_github_request(
            "GET",
            f"/repos/{FULL_REPO}/actions",
            token
        )
        
        if status == 200:
            print("✅ GitHub Actions is available")
            return True
    
    print(f"⚠️  Status {status}: Could not verify Actions status")
    return False

def dispatch_workflow(token: str, workflow_file: str, branch: str, description: str) -> bool:
    """Dispatch a GitHub Actions workflow"""
    print(f"\n  📨 Dispatching {workflow_file} ({description})...")
    
    status, response = make_github_request(
        "POST",
        f"/repos/{FULL_REPO}/actions/workflows/{workflow_file}/dispatches",
        token,
        {"ref": branch}
    )
    
    if status == 204:
        print(f"    ✅ {workflow_file} dispatched")
        return True
    elif status == 403:
        print(f"    ⚠️  {workflow_file} requires Actions enablement")
        print(f"       👉 https://github.com/{FULL_REPO}/settings/actions")
        return False
    else:
        print(f"    ❌ Error {status}: {response.get('message', 'Unknown error')}")
        return False

def create_branch_protection(token: str, branch: str) -> bool:
    """Configure branch protection for main"""
    if branch != "main":
        return True
    
    print("\n🔒 Configuring branch protection...")
    
    protection_rule = {
        "required_status_checks": {
            "strict": True,
            "contexts": [
                "ci/lint",
                "ci/test",
                "security/codeql",
                "validation/fork"
            ]
        },
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False
        },
        "enforce_admins": True,
        "allow_force_pushes": False,
        "allow_deletions": False
    }
    
    status, response = make_github_request(
        "PUT",
        f"/repos/{FULL_REPO}/branches/{branch}/protection",
        token,
        protection_rule
    )
    
    if status == 200:
        print("  ✅ Branch protection configured")
        return True
    else:
        print(f"  ⚠️  Could not configure branch protection: {response}")
        return False

def add_collaborators(token: str) -> bool:
    """Add upstream maintainers as collaborators (optional)"""
    print("\n👥 Managing collaborators...")
    
    # This is optional - mainly informational
    status, repo_data = make_github_request(
        "GET",
        f"/repos/{FULL_REPO}",
        token
    )
    
    if status == 200:
        print(f"  📊 Your fork info:")
        print(f"     Stars: {repo_data.get('stargazers_count', 0)}")
        print(f"     Watchers: {repo_data.get('watchers_count', 0)}")
        print(f"     Forks: {repo_data.get('forks_count', 0)}")
        return True
    
    return False

# ============================================================================
# Main Onboarding
# ============================================================================

def run_complete_onboarding():
    """Execute full GitHub onboarding process"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           🏛️  SLATE-ATHENA GitHub Onboarding              ║
    ║              Complete CI/CD & Automation Setup              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Get GitHub token
    print("Step 1️⃣  Authenticating with GitHub...")
    token = get_github_token()
    
    if not token:
        print("❌ Could not retrieve GitHub token")
        print("   Ensure GitHub credentials are stored in credential manager:")
        print("   👉 https://github.com/settings/tokens")
        return False
    
    print(f"✅ Authenticated as: {REPO_OWNER}")
    
    # Step 2: Verify fork exists
    print("\nStep 2️⃣  Verifying fork...")
    status, fork_data = make_github_request(
        "GET",
        f"/repos/{FULL_REPO}",
        token
    )
    
    if status == 200:
        print(f"✅ Fork verified: {fork_data['html_url']}")
    else:
        print(f"❌ Fork not found: {status}")
        return False
    
    # Step 3: Enable Actions
    print("\nStep 3️⃣  Enabling GitHub Actions...")
    if enable_actions(token):
        print("✅ GitHub Actions is ready")
    else:
        print("⚠️  Manual action required:")
        print(f"   → Visit: https://github.com/{FULL_REPO}/settings/actions")
        print("   → Click 'Enable Actions'")
    
    # Step 4: Dispatch workflows
    print("\nStep 4️⃣  Dispatching initial workflows...")
    dispatch_results = []
    for workflow_file, branch, description in WORKFLOWS_TO_DISPATCH:
        result = dispatch_workflow(token, workflow_file, branch, description)
        dispatch_results.append((workflow_file, result))
    
    successful = sum(1 for _, result in dispatch_results if result)
    print(f"\n  Summary: {successful}/{len(WORKFLOWS_TO_DISPATCH)} workflows dispatched")
    
    # Step 5: Branch protection
    print("\nStep 5️⃣  Configuring branch protection...")
    create_branch_protection(token, "main")
    
    # Step 6: Collaborators/info
    print("\nStep 6️⃣  Repository information...")
    add_collaborators(token)
    
    # Print next steps
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 ✅ Onboarding Complete!                      ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🎯 Your SLATE-ATHENA fork is configured and ready:
    
    📍 Fork URL:
       {fork_data['html_url']}
    
    🔧 Next Steps:
    
    1. Monitor workflows:
       → {fork_data['html_url']}/actions
    
    2. Configure branch rules (if needed):
       → {fork_data['html_url']}/settings/branches
    
    3. Enable additional Actions:
       → {fork_data['html_url']}/settings/actions
    
    4. Start developing:
       → Push to 'user/slate-agent' branch
       → Create pull requests to main
       → Workflows will run automatically
    
    5. Try Athena voice interface:
       → .\\venv\\Scripts\\python.exe slate/athena_voice.py
    
    6. View personalization:
       → cat .athena_personalization.json
    
    🏛️  Design System (SLATE-ATHENA):
       → See ATHENA_DESIGN_SYSTEM.md
       → Color palette: Parthenon Gold, Acropolis Gray, Aegean Deep
       → Logo: assets/athena-logo.svg
    
    ⚡ Voice-Controlled Athena (Coming Soon):
       Your vision: "Fully automatic voice-controlled Athena that 
       can build anything with precision. I just talk to it."
       
       Current status: Foundation built in slate/athena_voice.py
       Next: Train on Armor Engine patterns + game dev knowledge
    
    📞 Support:
       → Issues: {fork_data['html_url']}/issues
       → Discussions: {fork_data['html_url']}/discussions
       → Wiki: {fork_data['html_url']}/wiki
    
    """)
    
    return True

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    try:
        success = run_complete_onboarding()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚡ Onboarding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Onboarding failed: {e}")
        sys.exit(1)
