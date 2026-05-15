import yaml

def load_yaml(file):
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data