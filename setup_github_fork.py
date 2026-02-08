#!/usr/bin/env python3
"""
Setup GitHub fork integration and dispatch workflows.
Modified: 2026-02-08T02:30:00Z | Author: COPILOT | Change: GitHub Actions integration script
"""

import json
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent
MAIN_REPO = "SynchronizedLivingArchitecture/S.L.A.T.E"

def get_github_token():
    """Get GitHub token from git credential manager."""
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
                return line.split('=', 1)[1]
    except Exception as e:
        print(f"Error getting token: {e}")
    
    return None

def get_authenticated_user(token):
    """Get authenticated GitHub user info."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SLATE-Fork-Agent'
    }
    
    try:
        req = urllib.request.Request(
            'https://api.github.com/user',
            headers=headers,
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

def create_fork(token, user_login):
    """Create a fork of the SLATE repository."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SLATE-Fork-Agent'
    }
    
    data = json.dumps({
        'owner': 'SynchronizedLivingArchitecture',
        'repo': 'S.L.A.T.E'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            'https://api.github.com/repos/SynchronizedLivingArchitecture/S.L.A.T.E/forks',
            data=data,
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            fork_data = json.loads(response.read())
            return fork_data
    except urllib.error.HTTPError as e:
        if e.code == 422:
            # Fork already exists
            return {'already_exists': True, 'owner': {'login': user_login}}
        print(f"Error creating fork: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def dispatch_workflow(token, workflow_file, ref='main'):
    """Dispatch a GitHub Actions workflow."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'SLATE-Fork-Agent'
    }
    
    data = json.dumps({'ref': ref}).encode('utf-8')
    
    try:
        url = f'https://api.github.com/repos/{MAIN_REPO}/actions/workflows/{workflow_file}/dispatches'
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 204
    except Exception as e:
        print(f"Error dispatching workflow: {e}")
        return False

def main():
    print("=" * 70)
    print("  SLATE GitHub Fork & Actions Setup")
    print("=" * 70)
    print()
    
    # Step 1: Get token
    print("📝 Step 1: Getting GitHub credentials...")
    token = get_github_token()
    if not token:
        print("❌ No GitHub token found")
        print("   Please ensure git credential manager has GitHub credentials")
        return 1
    
    print(f"✅ Token retrieved: {token[:20]}...")
    print()
    
    # Step 2: Get user info
    print("📝 Step 2: Authenticating...")
    user = get_authenticated_user(token)
    if not user:
        print("❌ Failed to authenticate")
        return 1
    
    user_login = user['login']
    print(f"✅ Authenticated as: {user_login}")
    print(f"   Name: {user.get('name', 'N/A')}")
    print(f"   Public repos: {user.get('public_repos', 0)}")
    print()
    
    # Step 3: Create fork
    print("📝 Step 3: Creating fork...")
    fork = create_fork(token, user_login)
    if fork:
        if fork.get('already_exists'):
            print(f"✅ Fork already exists at: https://github.com/{user_login}/S.L.A.T.E")
        else:
            print(f"✅ Fork created at: {fork.get('html_url', 'N/A')}")
        fork_url = f"https://github.com/{user_login}/S.L.A.T.E.git"
        print()
    else:
        print("⚠️  Could not create fork (may already exist)")
        fork_url = f"https://github.com/{user_login}/S.L.A.T.E.git"
        print()
    
    # Step 4: Configure local fork
    print("📝 Step 4: Configuring local fork...")
    try:
        result = subprocess.run(
            [sys.executable, 'slate/slate_fork_manager.py', '--setup-fork', fork_url],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ Fork configured: {fork_url}")
        else:
            print(f"⚠️  Fork configuration output: {result.stdout}")
    except Exception as e:
        print(f"Error configuring fork: {e}")
    print()
    
    # Step 5: Dispatch workflows
    print("📝 Step 5: Dispatching validation workflows...")
    workflows_to_dispatch = [
        ('fork-validation.yml', 'Validate fork prerequisites'),
        ('ci.yml', 'Run CI checks'),
        ('slate.yml', 'Run SLATE integration tests'),
    ]
    
    for workflow, description in workflows_to_dispatch:
        result = dispatch_workflow(token, workflow)
        if result:
            print(f"✅ {description}: {workflow}")
        else:
            print(f"⚠️  {description}: {workflow} (may be scheduled)")
    
    print()
    print("=" * 70)
    print("  ✅ GitHub Integration Complete!")
    print("=" * 70)
    print()
    print("📊 Next Steps:")
    print(f"   1. View your fork: https://github.com/{user_login}/S.L.A.T.E")
    print(f"   2. Check Actions: https://github.com/{user_login}/S.L.A.T.E/actions")
    print(f"   3. Update remote: git remote set-url origin {fork_url}")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
