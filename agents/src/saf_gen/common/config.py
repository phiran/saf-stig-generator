"""
Configuration utilities for the SAF Generator project.

This module provides centralized configuration management including:
- Environment variable loading from development.env
- Common path resolution
- Configuration value access
"""

import os
import logging
from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Global flag to track if environment has been loaded
_ENV_LOADED = False


def load_environment(force_reload: bool = False) -> bool:
    """
    Load environment variables from the development.env file.

    Args:
        force_reload: If True, reload even if already loaded

    Returns:
        bool: True if environment was loaded successfully, False otherwise
    """
    global _ENV_LOADED

    if _ENV_LOADED and not force_reload:
        return True

    try:
        # Find the config directory relative to this file
        # This file is at: agents/src/saf_gen/common/config.py
        # Config dir is at: agents/config/
        current_file = Path(__file__).resolve()
        config_dir = current_file.parent.parent.parent.parent / "config"
        env_file = config_dir / "development.env"

        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment variables from %s", env_file)
            _ENV_LOADED = True
            return True
        else:
            logger.warning("Environment file not found: %s", env_file)
            # Still mark as loaded to avoid repeated warnings
            _ENV_LOADED = True
            return False

    except Exception as e:
        logger.error("Failed to load environment variables: %s", e)
        return False


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value from environment variables.

    Automatically loads environment if not already loaded.

    Args:
        key: Environment variable key
        default: Default value if key not found

    Returns:
        str or None: The configuration value
    """
    # Ensure environment is loaded
    load_environment()
    return os.getenv(key, default)


def get_artifacts_dir() -> Path:
    """
    Get the artifacts directory path.

    Priority:
    1. ARTIFACTS_DIR environment variable (loaded from development.env)
    2. Default: project_root/artifacts

    Returns:
        Path: The artifacts directory path
    """
    # Ensure environment is loaded
    load_environment()

    artifacts_dir_env = os.getenv("ARTIFACTS_DIR")

    if artifacts_dir_env:
        # Handle relative paths from config directory
        artifacts_path = Path(artifacts_dir_env)
        if not artifacts_path.is_absolute():
            # Resolve relative to the project root
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent
            artifacts_path = project_root / artifacts_path
        return artifacts_path.resolve()

    # Fallback: project root + artifacts
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    return project_root / "artifacts"


def get_download_dir() -> Path:
    """
    Get the downloads directory within artifacts.

    Returns:
        Path: The downloads directory path (artifacts/downloads)
    """
    return get_artifacts_dir() / "downloads"


def get_generated_dir() -> Path:
    """
    Get the generated files directory within artifacts.

    Returns:
        Path: The generated directory path (artifacts/generated)
    """
    return get_artifacts_dir() / "generated"


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path: The project root directory
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent.parent


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path to ensure exists

    Returns:
        Path: The directory path
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
