import os
import re

base = r'C:\syncnode\frontend\electron\src\renderer\src'

# (relative_file_path, depth_from_src_renderer_src)
files_to_fix = [
    (r'screens\RunsList.tsx', 1),
    (r'screens\Home.tsx', 1),
    (r'screens\RunShell.tsx', 1),
    (r'screens\Knowledge.tsx', 1),
    (r'screens\Learning.tsx', 1),
    (r'screens\Settings.tsx', 1),
    (r'screens\run\RunOverview.tsx', 2),
    (r'screens\run\RunSubTabs.tsx', 2),
    (r'screens\run\RunTimeline.tsx', 2),
    (r'screens\run\RunApprovals.tsx', 2),
    (r'components\run\AgentPanel.tsx', 2),
]

for rel, depth in files_to_fix:
    path = os.path.join(base, rel)
    if not os.path.exists(path):
        print(f'SKIP (not found): {rel}')
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Build the correct prefix for this depth
    correct_prefix = '../' * depth
    
    # Replace any relative path imports that reference lib/, stores/, components/, hooks/
    # Patterns: '../lib/', '../../lib/', '../../../lib/', etc.
    # We'll normalize all such patterns
    def replace_import(m):
        module = m.group(2)
        return f"from '{correct_prefix}{module}"
    
    new_content = re.sub(
        r"from '(\.\.\/)+((lib|stores|components|hooks)\/[^']+)",
        lambda m: f"from '{correct_prefix}{m.group(2)}'",
        content
    )
    # Fix the closing quote issue - the lambda above may not include the closing quote properly
    # Let's do it more carefully:
    new_content = content
    # Pattern: from '../../lib/... or from '../lib/... etc. (any depth)
    pattern = r"(from ')(\.\./)+((lib|stores|components|hooks)/[^']*')"
    replacement = lambda m: f"{m.group(1)}{correct_prefix}{m.group(3)}"
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'FIXED: {rel}')
    else:
        print(f'OK (no change): {rel}')

print('Done.')
