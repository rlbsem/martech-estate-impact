"""Public package inventory, historical byte protection and local documentation links."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BASE = "6bc3e253540dfe38cb5ae58cf00038dab31f7024"
EXCLUDED = {
    ".git",
    ".venv",
    ".local",
    "work",
    "build",
    "dist",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
}
MANIFEST = ROOT / "docs/evidence/change-assurance/package-manifest.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def files():
    def walk(folder):
        for p in sorted(folder.iterdir()):
            if p.name in EXCLUDED or p.name.endswith(".egg-info"):
                continue
            if p.is_dir():
                yield from walk(p)
            else:
                yield p

    return list(walk(ROOT))


def source_hashes():
    return {
        p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
        for p in files()
        if (
            p.suffix in {".py", ".sql", ".html", ".css", ".js", ".json", ".toml", ".lock", ".yml"}
            or p.name in {"Dockerfile.change", ".dockerignore"}
        )
        and not p.is_relative_to(ROOT / "docs")
        and not p.is_relative_to(ROOT / "examples")
    }


def preserve(create=False):
    path = ROOT / "docs/evidence/change-assurance/preserved-original.json"
    if create:
        names = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE], cwd=ROOT, text=True
        ).splitlines()
        permitted = {"README.md", "pyproject.toml", ".github/workflows/verify.yml"}
        entries = {
            n: sha(subprocess.check_output(["git", "show", f"{BASE}:{n}"], cwd=ROOT))
            for n in names
            if n not in permitted
        }
        save(path, dict(base_revision=BASE, exceptions=sorted(permitted), sha256=entries))
    record = json.loads(path.read_bytes())
    for name, expected in record["sha256"].items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise AssertionError("protected original changed: " + name)
    return len(record["sha256"])


def links():
    checked = 0
    for p in files():
        if p.suffix != ".md":
            continue
        text = re.sub(r"```.*?```", "", p.read_text(encoding="utf-8"), flags=re.S)
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if re.match(r"https?://|mailto:", target):
                continue
            relative = unquote(target.split("#", 1)[0])
            destination = (p.parent / relative).resolve() if relative else p
            if not destination.is_relative_to(ROOT) or not destination.exists():
                raise AssertionError(f"broken local link: {p.relative_to(ROOT)} -> {target}")
            checked += 1
    return checked


def scan():
    patterns = [
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        rb"AKIA[0-9A-Z]{16}",
        rb"gh[pousr]_[A-Za-z0-9]{30,}",
        rb"salesforce\.com/services/oauth2/token",
    ]
    checked = 0
    for p in files():
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".woff2"}:
            continue
        if p.name in {
            "runtime.json",
            "admin.json",
            "change_console.json",
            "database.env",
        } or p.suffix in {".pem", ".key", ".db"}:
            raise AssertionError("private file in package: " + p.name)
        raw = p.read_bytes()
        for pattern in patterns:
            assert not re.search(pattern, raw), "sensitive pattern in " + str(p.relative_to(ROOT))
        checked += 1
    return checked


def inventory(check=False):
    entries = {
        p.relative_to(ROOT).as_posix(): {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
        for p in files()
        if p != MANIFEST
    }
    if check:
        assert json.loads(MANIFEST.read_bytes())["files"] == entries, (
            "current package inventory mismatch"
        )
    else:
        save(
            MANIFEST,
            dict(
                format="change-package/v1",
                excluded_self=MANIFEST.relative_to(ROOT).as_posix(),
                files=entries,
            ),
        )
    return len(entries)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--create-preservation", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            dict(
                preserved=preserve(args.create_preservation),
                links=links(),
                public_scan=scan(),
                package_files=inventory(not args.write),
            )
        )
    )
