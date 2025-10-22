import yaml
    
def load_config(config_path: str = "./src/config.yaml") -> dict:
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        return config_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")