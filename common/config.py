import yaml

def load_env(env):
    with open("config/env.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data[env]