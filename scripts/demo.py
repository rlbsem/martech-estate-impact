from pathlib import Path
import json

from estate_impact.demo import run

if __name__ == "__main__":
    print(json.dumps(run(Path(__file__).resolve().parents[1]), indent=2))
