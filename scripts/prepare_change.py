"""Generate disposable Compose credentials locally, never in public artifacts."""

import argparse
import json
from pathlib import Path
import secrets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("work/compose"))
    args = parser.parse_args()
    if args.directory.exists():
        raise ValueError("fresh private configuration directory required")
    args.directory.mkdir(parents=True)
    password = secrets.token_hex(32)
    (args.directory / "database.env").write_text(
        f"POSTGRES_USER=estate\nPOSTGRES_DB=estate\nPOSTGRES_PASSWORD={password}\n",
        encoding="utf-8",
    )
    (args.directory / "admin.json").write_text(
        json.dumps({"dsn": f"postgresql://estate:{password}@postgres:5432/estate"}),
        encoding="utf-8",
    )
    print("Disposable configuration generated under ignored work/. No credentials printed.")


if __name__ == "__main__":
    main()
