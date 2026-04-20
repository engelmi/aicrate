import json
from pathlib import Path

import yaml


def load_file(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' not found")

    with open(path, "r") as f:
        if path.suffix == ".json":
            return json.load(f)
        elif path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)

        raise NotImplementedError(f"File extension '{path.suffix}' not supported")
