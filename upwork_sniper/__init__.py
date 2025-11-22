"""Utilities for the interactive Upwork Playwright crawler."""

from pathlib import Path
import yaml


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config():
    """Load crawler configuration YAML."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file) or {}


__all__ = ["BASE_DIR", "CONFIG_PATH", "load_config"]


