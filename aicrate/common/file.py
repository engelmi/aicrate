import json
from pathlib import Path

import yaml


def load_file(p: Path) -> dict:
    if not p.exists():
        raise FileNotFoundError(f"File '{p}' not found")

    with open(p, "r") as f:
        if p.suffix == ".json":
            return json.load(f)
        elif p.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)

        raise NotImplementedError(f"File extension '{p.suffix}' not supported")
