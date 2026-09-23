"""
Fix stdlib logger calls that use keyword arguments.
Converts:  logger.info("msg", key=val, key2=val2)
To:        logger.info(f"msg — key={val} key2={val2}")
"""

import re
import pathlib

TARGET_DIRS = [
    pathlib.Path("C:/syncnode/backend/src"),
]

PATTERN = re.compile(
    r"(?P<indent>\s*)(?P<method>logger\.(?:info|warning|error|debug|critical))\("
    r"(?P<first>[\"'][^\"']*[\"']|f[\"'][^\"']*[\"']),\s*"
    r"(?P<rest>.*)\)$"
)

def fix_file(fpath: pathlib.Path) -> bool:
    lines = fpath.read_text(encoding="utf-8").splitlines()
    new_lines = []
    changed = False

    for line in lines:
        m = PATTERN.match(line)
        if m:
            indent = m.group("indent")
            method = m.group("method")
            first = m.group("first").strip()
            rest = m.group("rest").strip()

            # Parse kwargs like: key=val, key2=val2
            kwargs_list = re.findall(r"(\w+)=([^,]+)", rest)
            if kwargs_list:
                extra = " ".join(f"{k}={v.strip()}" for k, v in kwargs_list)
                # Extract the message string content
                if first.startswith('f"') or first.startswith("f'"):
                    inner = first[2:-1]
                    new_line = f'{indent}{method}(f"{inner} \u2014 {extra}")'
                elif first.startswith('"') or first.startswith("'"):
                    inner = first[1:-1]
                    new_line = f'{indent}{method}(f"{inner} \u2014 {extra}")'
                else:
                    new_line = line
                new_lines.append(new_line)
                changed = True
                continue
        new_lines.append(line)

    if changed:
        fpath.write_text("\n".join(new_lines), encoding="utf-8")
    return changed


fixed = []
for target_dir in TARGET_DIRS:
    for fpath in target_dir.rglob("*.py"):
        if fix_file(fpath):
            fixed.append(fpath.name)

print(f"Fixed {len(fixed)} file(s): {fixed}")
