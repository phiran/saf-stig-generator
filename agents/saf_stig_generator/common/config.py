"""
Configuration management for SAF STIG Generator.

This module provides centralized configuration loading for the SAF STIG Generator
project, including environment variables and common paths.

Usage:
    from saf_stig_generator.common.config import load_env, get_artifacts_dir

    # Load environment at module import
    load_env()

    # Get common directories
    download_dir = get_download_dir()
    artifacts_dir = get_artifacts_dir()
"""

import logging
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = None

logger = logging.getLogger(__name__)

# Global flag to track if environment has been loaded
_ENV_LOADED = False


def find_config_file() -> Optional[Path]:
    """
    Find the development.env configuration file by searching up the directory tree.

    Returns:
        Path to development.env file or None if not found
    """
    # Start from current file and search upward
    current = Path(__file__).resolve()

    # Search up to 5 levels for the config directory
    for _ in range(5):
        current = current.parent
        config_dir = current / "agents" / "config"
        env_file = config_dir / "development.env"

        if env_file.exists():
            return env_file

        # Also check for config directory at the current level
        config_dir_alt = current / "config"
        env_file_alt = config_dir_alt / "development.env"
        if env_file_alt.exists():
            return env_file_alt

    return None


def load_env(force_reload: bool = False) -> bool:
    """
    Load environment variables from development.env file.

    Args:
        force_reload: If True, reload even if already loaded

    Returns:
        bool: True if environment was loaded successfully, False otherwise
    """
    global _ENV_LOADED

    if _ENV_LOADED and not force_reload:
        return True

    if not DOTENV_AVAILABLE:
        logger.warning("python-dotenv not available, skipping environment file loading")
        _ENV_LOADED = True
        return False

    try:
        env_file = find_config_file()

        if env_file and env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment variables from %s", env_file)
            _ENV_LOADED = True
            return True
        else:
            logger.warning("Environment file not found in expected locations")
            _ENV_LOADED = True
            return False

    except Exception as e:
        logger.error("Failed to load environment variables: %s", e)
        _ENV_LOADED = True
        return False


def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value from environment variables.

    Args:
        key: Environment variable key
        default: Default value if key not found

    Returns:
        The configuration value or default
    """
    # Ensure environment is loaded
    load_env()
    return os.getenv(key, default)


def find_project_root() -> Path:
    """
    Find the project root directory by looking for key indicators.

    Returns:
        Path to project root
    """
    current = Path(__file__).resolve()

    # Search upward for project indicators
    for _ in range(5):
        current = current.parent

        # Look for project indicators
        if any(
            [
                (current / "pyproject.toml").exists(),
                (current / "agents").exists() and (current / "agents").is_dir(),
                (current / ".git").exists(),
            ]
        ):
            return current

    # Fallback: assume current file is in project somewhere
    return Path(__file__).resolve().parent


def get_artifacts_dir() -> Path:
    """
    Get the artifacts directory path.

    Returns:
        Path to artifacts directory
    """
    load_env()  # Ensure environment is loaded

    artifacts_dir_env = os.getenv("ARTIFACTS_DIR")

    if artifacts_dir_env:
        artifacts_path = Path(artifacts_dir_env)
        if not artifacts_path.is_absolute():
            # Resolve relative to project root
            project_root = find_project_root()
            artifacts_path = project_root / artifacts_path
        return artifacts_path.resolve()

    # Default: project_root/artifacts
    project_root = find_project_root()
    return project_root / "artifacts"


def get_download_dir() -> Path:
    """Get the downloads directory (artifacts/downloads)."""
    return get_artifacts_dir() / "downloads"


def get_generated_dir() -> Path:
    """Get the generated files directory (artifacts/generated)."""
    return get_artifacts_dir() / "generated"


def ensure_dir(directory: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path to ensure exists

    Returns:
        The directory path
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# Auto-load environment when module is imported
load_env()
