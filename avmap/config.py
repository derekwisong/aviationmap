
import yaml

from . import config_file

def read_config() -> dict:
    """Load configuration file"""
    with open(config_file, 'rb') as config:
        return yaml.load(config, Loader=yaml.Loader)