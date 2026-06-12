from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(file):
    yaml_file = Path(file)
    if not yaml_file.is_absolute():
        yaml_file = PROJECT_ROOT / yaml_file

    with yaml_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data
