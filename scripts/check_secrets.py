"""Verifica arquivos versionáveis sem imprimir valores potencialmente secretos."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r"\b(?:gh[pousr]_|github_pat_|sb_secret_)[A-Za-z0-9_-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]

def main() -> int:
    files = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode("utf-8").split("\0")
    issues = []
    for name in sorted(set(filter(None, files))):
        path = ROOT / name
        if not path.is_file():
            continue
        if (path.name.startswith(".env") and path.name != ".env.example") or any(
            part in {"node_modules", ".venv", "__pycache__", "dist", ".temp"} for part in path.parts
        ):
            issues.append(f"{name}: arquivo privado/gerado versionável")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(content.splitlines(), 1):
            if any(pattern.search(line) for pattern in PATTERNS):
                issues.append(f"{name}:{number}: possível segredo (valor omitido)")
    for issue in issues:
        print(issue)
    print(f"Verificação: {len(issues)} ocorrência(s).")
    return int(bool(issues))

if __name__ == "__main__":
    sys.exit(main())
