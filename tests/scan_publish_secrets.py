"""Scan publication candidates without printing credential values."""
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).decode().split('\0')
secrets = []
env = root / '.env'
if env.exists():
    for line in env.read_text(encoding='utf-8-sig').splitlines():
        match = re.match(r'\s*([A-Z_0-9]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z_0-9]*)\s*=\s*(.+)', line, re.I)
        if match:
            value = match[2].strip().strip('\"\'')
            if len(value) >= 8:
                secrets.append((match[1], value.encode()))
patterns = [
    ('private key', re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
    ('GitHub token', re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b')),
    ('AWS access key', re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),
    ('API secret token', re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b')),
]
findings = []
for name in sorted(set(files)):
    if not name:
        continue
    path = root / name
    if not path.is_file():
        continue
    data = path.read_bytes()
    for label, value in secrets:
        if value in data:
            findings.append((name, 'matches local ' + label))
    for label, pattern in patterns:
        if pattern.search(data):
            findings.append((name, label))
for name, reason in findings:
    print(f'BLOCKED {name}: {reason}')
print(f'Scanned {len(set(files)) - 1} candidate files; findings={len(findings)}; local credential values checked={len(secrets)}')
raise SystemExit(bool(findings))
