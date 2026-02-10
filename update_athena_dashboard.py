#!/usr/bin/env python3
"""Update SLATE Dashboard to ATHENA design system colors."""
# Modified: 2026-02-08T16:00:00Z | Author: COPILOT | Change: Apply SLATE-ATHENA colors to dashboard

import re
from pathlib import Path

def update_dashboard_colors():
    """Replace dashboard colors with ATHENA palette."""
    
    file = Path("agents/slate_dashboard_server.py")
    
    # Read the file
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ATHENA Color Palette Mapping
    color_mappings = {
        # Original SLATE -> ATHENA colors
        '#B85A3C': '#D4AF37',  # Parthenon Gold
        '#D4785A': '#E4BF47',  # Parthenon Gold Light
        '#8B4530': '#8A7F1A',  # Darkened gold
        '#FFE4D9': '#F5E6D3',  # Warm cream
        
        # Accent replacements
        '#5D5D74': '#1A3A52',  # Aegean Deep
        '#7A7A94': '#2A5A72',  # Aegean Deep Light
        '#E2E2F0': '#1A3A52',  # Aegean Deep container
        
        # Success -> Olive Green
        '#22c55e': '#4A6741',  # Olive Green
        'rgba(34, 197, 94, ': 'rgba(74, 103, 65, ',  # Success background
        
        # Warning -> Torch Flame
        '#eab308': '#FF6B1A',  # Torch Flame
        'rgba(234, 179, 8, ': 'rgba(255, 107, 26, ',  # Warning background
        
        # Error stays similar or use complementary
        '#ef4444': '#E85050',  # Adjusted red
    }
    
    # Apply all mappings
    for old_color, new_color in color_mappings.items():
        content = content.replace(old_color, new_color)
    
    # Add ATHENA comment to the CSS root
    athena_comment = '<!-- Modified: 2026-02-08T16:00:00Z | Author: COPILOT | Change: SLATE-ATHENA colors applied (Parthenon Gold, Aegean Deep, Acropolis Gray, Torch Flame, Olive Green) -->'
    
    # Find the style tag and add comment after
    content = re.sub(
        r'(<style>)',
        r'\1\n    ' + athena_comment + '\n',
        content,
        count=1
    )
    
    # Write back
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[✓] Dashboard colors updated to ATHENA palette")
    print("   Primary: Parthenon Gold (#D4AF37)")
    print("   Secondary: Aegean Deep (#1A3A52)")
    print("   Success: Olive Green (#4A6741)")
    print("   Warning: Torch Flame (#FF6B1A)")
    print(f"   File: {file}")

if __name__ == '__main__':
    update_dashboard_colors()
