import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from utils.auth import get_env_config, get_auth_token


def get_env_config(env_key, default_value=None):
    env_value = os.getenv(env_key)
    if env_value is not None:
        return env_value
    
    config_path = os.path.join(os.path.dirname(__file__), "../../../config/env.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        env_mapping = {
            "BASE_URL": "test.base_url",
            "API_BASE_URL": "test.api_base_url",
            "TEST_USERNAME": "test.username",
            "TEST_PASSWORD": "test.password"
        }
        if env_key in env_mapping:
            keys = env_mapping[env_key].split(".")
            value = config
            for key in keys:
                value = value.get(key)
                if value is None:
                    break
            if value is not None:
                return value
    
    return default_value


__all__ = ["get_env_config", "get_auth_token"]
