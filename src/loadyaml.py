import yaml
from pathlib import Path

def load_yaml(yaml_file: str = "prompts.yaml") -> dict:
    prompt_file = Path(__file__).parent / yaml_file
    with open(prompt_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)