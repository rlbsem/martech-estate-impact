import argparse
import json
from pathlib import Path

from . import db
from .demo import read, run, write_json
from .impact import assess


def main():
    parser = argparse.ArgumentParser(
        description="Synthetic estate evidence and counterfactual analysis"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository containing migrations/config/fixtures",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    demo = commands.add_parser("demo")
    demo.add_argument("--output", type=Path)
    assessment = commands.add_parser("assess")
    assessment.add_argument("--snapshot", required=True)
    assessment.add_argument("--proposal", type=Path, required=True)
    assessment.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "init":
        db.migrate(args.root)
    elif args.command == "demo":
        print(json.dumps(run(args.root, args.output), indent=2))
    else:
        snapshot = db.load_snapshot(args.snapshot)
        proposal = read(args.proposal)
        proposal["base_snapshot"] = args.snapshot
        result = assess(snapshot, proposal)
        db.save_assessment(result)
        write_json(args.output, result)
        print(result["disposition"])


if __name__ == "__main__":
    main()
