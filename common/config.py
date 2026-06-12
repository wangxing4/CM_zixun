from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]

def load_env(env):
    config_file = PROJECT_ROOT / "config" / "env.yaml"
    with config_file.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data[env]
