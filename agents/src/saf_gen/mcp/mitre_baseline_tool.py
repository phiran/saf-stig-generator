"""MITRE Baseline Tool (mcp/mitre_baseline_tool.py):
Finds and clones existing baselines from GitHub for STIG compliance.
Example: https://github.com/mitre/redhat-enterprise-linux-9-stig-baseline

FastMCP Tool Name: find_mitre_baseline
Returns: A JSON object with the local path to the cloned repository, or error details.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import anyio
import requests
from fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastMCP Server Initialization ---
mcp = FastMCP("mitre-baseline-tool")

# --- Constants ---
TOOL_VERSION = "1.0.0"
TOOL_DESCRIPTION = "Searches and clones MITRE baseline repositories from GitHub"


def _get_artifacts_download_dir() -> Path:
    """
    Determines the download directory.
    Priority:
    1. ARTIFACTS_DIR environment variable.
    2. A directory named 'artifacts/downloads' located two levels
       above this script's location.
    """
    if artifacts_dir_env := os.getenv("ARTIFACTS_DIR"):
        return Path(artifacts_dir_env) / "downloads"

    # Path to the current script -> up to project root -> artifacts/downloads
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent.parent.parent  # Go up to project root
    return base_dir / "artifacts" / "downloads"


# --- MCP Resources ---
@mcp.resource("mitre-baseline-tool://version")
def get_version() -> str:
    """Returns the version of the MITRE Baseline Tool."""
    return f"MITRE Baseline Tool v{TOOL_VERSION}"


@mcp.resource("mitre-baseline-tool://info")
def get_info() -> dict:
    """Returns information about the MITRE Baseline Tool."""
    return {
        "name": "MITRE Baseline Tool",
        "version": TOOL_VERSION,
        "description": TOOL_DESCRIPTION,
        "capabilities": [
            "Search GitHub repositories",
            "Clone MITRE baseline repositories",
            "Handle paginated API responses",
            "Support GitHub token authentication",
        ],
        "required_dependencies": ["git", "requests", "fastmcp", "anyio"],
        "supported_transports": ["stdio", "sse", "http"],
    }


async def _get_all_repos_async(
    search_query: str, token: Optional[str]
) -> List[Dict[str, Any]]:
    """
    Asynchronously retrieves all repositories matching the search query, handling pagination.

    Args:
        search_query: The search query (e.g., "MITRE STIG in:name").
        token: GitHub Personal Access Token for authentication.

    Returns:
        List of repository items from the GitHub API.
    """

    def _sync_get_repos() -> List[Dict[str, Any]]:
        all_repos = []
        page = 1
        per_page = 100
        base_api_url = "https://api.github.com"
        search_endpoint = f"{base_api_url}/search/repositories"

        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        logger.info(f"Starting GitHub repository search for query: '{search_query}'")

        while True:
            params = {"q": search_query, "per_page": per_page, "page": page}
            try:
                response = requests.get(
                    search_endpoint, headers=headers, params=params, timeout=30
                )
                response.raise_for_status()
                data = response.json()
                items = data.get("items", [])

                if not items:
                    logger.info("No more repositories found.")
                    break

                all_repos.extend(items)
                logger.info(
                    f"Found {len(items)} repositories on page {page}. Total found so far: {len(all_repos)}."
                )

                if (
                    "Link" in response.headers
                    and 'rel="next"' in response.headers["Link"]
                ):
                    page += 1
                else:
                    break

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP Error: {e}")
                if e.response.status_code == 403:
                    logger.error(
                        "API rate limit likely exceeded. Try again later or use an authenticated token."
                    )
                raise
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"An error occurred while communicating with the GitHub API: {e}"
                )
                raise

        return all_repos

    return await anyio.to_thread.run_sync(_sync_get_repos)


async def _clone_repo_async(
    repo_url: str, repo_name: str, output_dir: str
) -> Dict[str, Any]:
    """
    Asynchronously clones a single repository using the git command-line tool.

    Args:
        repo_url: The URL of the repository to clone.
        repo_name: The name of the repository.
        output_dir: The directory to clone the repository into.

    Returns:
        Dictionary with clone status and details.
    """

    def _sync_clone() -> Dict[str, Any]:
        clone_directory = os.path.join(output_dir, repo_name)
        if os.path.exists(clone_directory):
            logger.warning(
                f"Directory '{clone_directory}' already exists. Skipping clone for '{repo_name}'."
            )
            return {
                "status": "skipped",
                "message": f"Directory already exists: {clone_directory}",
                "path": clone_directory,
            }

        logger.info(
            f"Cloning '{repo_name}' from '{repo_url}' into '{clone_directory}'..."
        )
        try:
            # Ensure parent directory exists
            os.makedirs(output_dir, exist_ok=True)

            command = ["git", "clone", repo_url, clone_directory]
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, timeout=300
            )
            logger.info(f"Successfully cloned '{repo_name}'.")
            logger.debug(f"Git output:\n{result.stdout}")

            return {
                "status": "success",
                "message": f"Successfully cloned {repo_name}",
                "path": clone_directory,
                "repo_name": repo_name,
                "repo_url": repo_url,
            }

        except FileNotFoundError:
            error_msg = "Git command not found. Please ensure Git is installed and in your system's PATH."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except subprocess.TimeoutExpired:
            error_msg = f"Clone operation timed out for '{repo_name}'"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to clone '{repo_name}'. Git command exited with status {e.returncode}. Stderr: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = (
                f"An unexpected error occurred during cloning of '{repo_name}': {e}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    return await anyio.to_thread.run_sync(_sync_clone)


@mcp.tool
async def find_mitre_baseline(
    query: str, token: Optional[str] = None, max_results: int = 10, ctx: Context = None
) -> str:
    """
    Search for and clone MITRE baseline repositories from GitHub.

    Args:
        query: GitHub search query (e.g., "MITRE STIG baseline")
        token: GitHub Personal Access Token for authentication
        max_results: Maximum number of repositories to clone (default: 10)
        ctx: FastMCP context for logging

    Returns:
        JSON string with search and clone results
    """
    try:
        if ctx:
            await ctx.info(f"Starting MITRE baseline search for: {query}")

        # Set up output directory
        output_dir = _get_artifacts_download_dir()
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Starting MITRE baseline search with query: '{query}'")
        logger.info(f"Output directory: {output_dir}")

        # Search for repositories
        repositories = await _get_all_repos_async(query, token)

        if not repositories:
            if ctx:
                await ctx.info("No repositories found matching the search criteria")
            result = {
                "status": "not_found",
                "message": "No repositories found matching the search criteria",
                "data": {
                    "query": query,
                    "repositories_found": 0,
                    "repositories_cloned": 0,
                    "output_dir": str(output_dir),
                },
            }
            return json.dumps(result)

        # Limit results if necessary
        repositories = repositories[:max_results]

        if ctx:
            await ctx.info(
                f"Found {len(repositories)} repositories. Starting cloning process..."
            )
        logger.info(
            f"Found {len(repositories)} repositories. Starting cloning process..."
        )

        # Clone repositories
        cloned_repos = []
        errors = []

        for repo in repositories:
            repo_name = repo["name"]
            repo_url = repo["clone_url"]

            try:
                if ctx:
                    await ctx.info(f"Cloning repository: {repo_name}")
                clone_result = await _clone_repo_async(
                    repo_url, repo_name, str(output_dir)
                )
                cloned_repos.append(clone_result)
                logger.info(
                    f"Processed repository: {repo_name} - {clone_result['status']}"
                )
            except Exception as e:
                error_info = {
                    "repo_name": repo_name,
                    "repo_url": repo_url,
                    "error": str(e),
                }
                errors.append(error_info)
                logger.error(f"Failed to clone {repo_name}: {e}")
                if ctx:
                    await ctx.error(f"Failed to clone {repo_name}: {e}")

        success_count = sum(1 for r in cloned_repos if r["status"] == "success")

        result = {
            "status": "success",
            "message": f"Processed {len(repositories)} repositories. {success_count} successfully cloned.",
            "data": {
                "query": query,
                "repositories_found": len(repositories),
                "repositories_cloned": success_count,
                "output_dir": str(output_dir),
                "cloned_repositories": cloned_repos,
                "errors": errors,
            },
        }

        if ctx:
            await ctx.info(
                f"MITRE baseline search completed with {success_count} repositories cloned."
            )

        return json.dumps(result)

    except requests.exceptions.RequestException as e:
        error_msg = f"GitHub API error: {e}"
        logger.error(error_msg)
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})

    except Exception as e:
        error_msg = f"Unexpected error in find_mitre_baseline: {e}"
        logger.error(error_msg, exc_info=True)
        if ctx:
            await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="MITRE Baseline Tool - FastMCP server for searching and cloning GitHub repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Transport Modes:
    stdio (default)    - Standard input/output transport for local use
    sse               - Server-Sent Events transport for web deployment  
    http              - Streamable HTTP transport for web deployment

    Examples:
    python mitre_baseline_tool.py                        # Run with stdio transport
    python mitre_baseline_tool.py --sse                  # Run with SSE on default host/port
    python mitre_baseline_tool.py --sse 0.0.0.0 8001     # Run with SSE on specific host/port
    python mitre_baseline_tool.py --http 127.0.0.1 8000  # Run with HTTP transport

    Environment Variables:
    GITHUB_TOKEN: GitHub Personal Access Token for API authentication
    ARTIFACTS_DIR: Custom directory for storing cloned repositories

    Version: %(version)s
        """
        % {"version": TOOL_VERSION},
    )

    parser.add_argument(
        "--version", action="version", version=f"MITRE Baseline Tool v{TOOL_VERSION}"
    )

    # Transport mode arguments
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument(
        "--sse", action="store_true", help="Use Server-Sent Events transport"
    )
    transport_group.add_argument(
        "--http", action="store_true", help="Use streamable HTTP transport"
    )

    parser.add_argument(
        "host",
        nargs="?",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "port",
        nargs="?",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )

    try:
        args = parser.parse_args()

        # Determine transport and run server
        if args.sse:
            logger.info(
                "Starting MITRE Baseline Tool MCP Server with SSE transport on %s:%s",
                args.host,
                args.port,
            )
            mcp.run(transport="sse", host=args.host, port=args.port)
        elif args.http:
            logger.info(
                "Starting MITRE Baseline Tool MCP Server with HTTP transport on %s:%s",
                args.host,
                args.port,
            )
            mcp.run(
                transport="streamable-http", host=args.host, port=args.port, path="/mcp"
            )
        else:
            logger.info("Starting MITRE Baseline Tool MCP Server with STDIO transport")
            mcp.run()  # Default: uses STDIO transport

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to start server: %s", e)
        sys.exit(1)
