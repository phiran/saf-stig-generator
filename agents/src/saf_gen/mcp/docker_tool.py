"""
Docker Tool (mcp/docker_tool.py):
Purpose: Manages Docker images and containers for the test environment.
Repository: https://hub.docker.com/search

MCP Tool Name: fetch_docker_image
Returns: A JSON object with the name and tag of the pulled Docker image.
"""

# Suppress websocket deprecation warnings early
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))
from suppress_warnings import configure_warnings_for_mcp

configure_warnings_for_mcp()

import json
import logging
import re
import sys
from typing import TYPE_CHECKING
from pathlib import Path

import docker
import requests
from fastmcp import FastMCP, Context

# Import the standalone configuration module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

if TYPE_CHECKING:
    from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment is automatically loaded by saf_config module

# --- FastMCP Server Initialization ---
mcp = FastMCP("docker-tool")

# --- Constants ---
VERSION = "1.0.0"

# Global variable for CLI-provided product keyword
CLI_PRODUCT_KEYWORD = None


@mcp.resource("docker-tool://version")
def get_version() -> str:
    """Returns the version of the Docker Tool."""
    return f"Docker Tool v{VERSION}"


@mcp.resource("docker-tool://info")
def get_info() -> dict:
    """Returns information about the Docker Tool."""
    return {
        "name": "Docker Tool",
        "version": VERSION,
        "description": "Manages Docker images and containers for test environments",
        "capabilities": [
            "Search Docker Hub repositories",
            "Pull Docker images",
            "List local Docker images",
            "Remove Docker images",
        ],
        "required_dependencies": ["docker", "requests", "fastmcp"],
        "supported_transports": ["stdio", "sse", "http"],
    }


def _normalize_product_name(product_name: str) -> str:
    """Convert product name to Docker Hub search-friendly format."""
    # Convert to lowercase and replace spaces with hyphens
    normalized = re.sub(r"[^\w\s-]", "", product_name.lower())
    normalized = re.sub(r"\s+", "-", normalized.strip())
    return normalized


def _search_docker_hub(product_keyword: str, limit: int = 10) -> list[dict]:
    """Search Docker Hub for images matching the product keyword."""
    search_url = "https://hub.docker.com/v2/search/repositories/"

    params = {
        "query": product_keyword,
        "page_size": limit,
        "ordering": "pull_count",  # Order by popularity
    }

    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as e:
        logger.error("Failed to search Docker Hub: %s", e)
        return []


def _select_best_image(search_results: list[dict], product_keyword: str) -> dict | None:
    """Select the most appropriate image from search results."""
    if not search_results:
        return None

    # Prioritize official images and images with higher pull counts
    scored_results = []

    for result in search_results:
        score = 0
        name = result.get("name", "").lower()
        description = result.get("description", "").lower()
        is_official = result.get("is_official", False)
        pull_count = result.get("pull_count", 0)

        # Higher score for official images
        if is_official:
            score += 1000

        # Higher score for exact or close matches in name
        if product_keyword.lower() in name:
            score += 500

        # Score based on pull count (normalized)
        score += min(pull_count // 1000, 100)

        # Prefer images with good descriptions
        if description and len(description) > 10:
            score += 10

        scored_results.append((score, result))

    # Sort by score (highest first) and return the best match
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return scored_results[0][1] if scored_results else None


@mcp.tool
async def fetch_docker_image(product_keyword: str, ctx: Context) -> str:
    """Finds and pulls a Docker image suitable for testing the specified product.

    Args:
        product_keyword: Product name to search for (e.g., 'RHEL 9', 'Ubuntu 20.04').

    Returns:
        JSON string containing the image name, tag, and pull status.
    """
    await ctx.info(f"Starting Docker image search for: {product_keyword}")

    try:
        # Initialize Docker client
        try:
            docker_client = docker.from_env()
            # Test Docker connection
            docker_client.ping()
            await ctx.info("Docker daemon connection established")
        except docker.errors.DockerException as e:
            error_msg = f"Failed to connect to Docker daemon: {str(e)}"
            await ctx.error(error_msg)
            return json.dumps({"error": error_msg})

        # Normalize the product name for search
        normalized_keyword = _normalize_product_name(product_keyword)
        await ctx.info(f"Searching Docker Hub for: {normalized_keyword}")

        # Search Docker Hub for matching images
        search_results = _search_docker_hub(normalized_keyword)

        if not search_results:
            # Try with the original keyword if normalized search fails
            await ctx.info(
                f"No results with normalized name, trying original: {product_keyword}"
            )
            search_results = _search_docker_hub(product_keyword)

        if not search_results:
            error_msg = f"No Docker images found for product: {product_keyword}"
            await ctx.error(error_msg)
            return json.dumps({"error": error_msg})

        # Select the best matching image
        best_image = _select_best_image(search_results, product_keyword)

        if not best_image:
            error_msg = f"No suitable Docker image found for product: {product_keyword}"
            await ctx.error(error_msg)
            return json.dumps({"error": error_msg})

        # Extract image details
        image_name = best_image["name"]
        # Use 'latest' tag if no specific tag is mentioned
        image_tag = "latest"
        full_image_name = f"{image_name}:{image_tag}"

        await ctx.info(f"Selected image: {full_image_name}")
        await ctx.info(f"Image description: {best_image.get('description', 'N/A')}")

        # Pull the Docker image
        await ctx.info(f"Pulling Docker image: {full_image_name}")
        logger.info("Pulling Docker image: %s", full_image_name)

        try:
            image = docker_client.images.pull(image_name, tag=image_tag)
            await ctx.info(f"Successfully pulled image: {full_image_name}")
            logger.info("Successfully pulled image: %s", full_image_name)

            # Get image details
            image_info = {
                "name": image_name,
                "tag": image_tag,
                "full_name": full_image_name,
                "image_id": image.id,
                "size": image.attrs.get("Size", 0),
                "created": image.attrs.get("Created", ""),
                "is_official": best_image.get("is_official", False),
                "pull_count": best_image.get("pull_count", 0),
                "description": best_image.get("description", ""),
                "status": "pulled_successfully",
            }

            await ctx.info("Docker image pull completed successfully")
            return json.dumps(image_info)

        except docker.errors.ImageNotFound:
            error_msg = f"Docker image not found: {full_image_name}"
            await ctx.error(error_msg)
            return json.dumps({"error": error_msg})
        except docker.errors.APIError as e:
            error_msg = f"Docker API error while pulling {full_image_name}: {str(e)}"
            await ctx.error(error_msg)
            return json.dumps({"error": error_msg})

    except (requests.RequestException, docker.errors.DockerException) as e:
        logger.error("Error in fetch_docker_image: %s", e, exc_info=True)
        await ctx.error(f"Docker image fetch failed: {str(e)}")
        return json.dumps({"error": str(e)})


@mcp.tool
async def list_docker_images(ctx: Context) -> str:
    """Lists all locally available Docker images.

    Returns:
        JSON string containing a list of local Docker images.
    """
    await ctx.info("Listing local Docker images")

    try:
        docker_client = docker.from_env()
        images = docker_client.images.list()

        image_list = []
        for image in images:
            # Get the first tag if available, otherwise use image ID
            tags = image.tags
            name = tags[0] if tags else f"<none>:{image.short_id}"

            image_info = {
                "name": name,
                "id": image.short_id,
                "size": image.attrs.get("Size", 0),
                "created": image.attrs.get("Created", ""),
                "tags": tags,
            }
            image_list.append(image_info)

        result = {"images": image_list, "count": len(image_list)}

        await ctx.info(f"Found {len(image_list)} local Docker images")
        return json.dumps(result)

    except docker.errors.DockerException as e:
        error_msg = f"Failed to list Docker images: {str(e)}"
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool
async def remove_docker_image(image_name: str, ctx: Context) -> str:
    """Removes a Docker image from the local system.

    Args:
        image_name: Name or ID of the Docker image to remove.

    Returns:
        JSON string containing the removal status.
    """
    await ctx.info(f"Removing Docker image: {image_name}")

    try:
        docker_client = docker.from_env()

        try:
            docker_client.images.remove(image_name, force=True)
            await ctx.info(f"Successfully removed Docker image: {image_name}")

            result = {"image_name": image_name, "status": "removed_successfully"}
            return json.dumps(result)

        except docker.errors.ImageNotFound:
            error_msg = f"Docker image not found: {image_name}"
            await ctx.error(error_msg)
            return json.dumps({"error": error_msg})
        except docker.errors.APIError as e:
            error_msg = f"Failed to remove Docker image {image_name}: {str(e)}"
            await ctx.error(error_msg)
            return json.dumps({"error": error_msg})

    except docker.errors.DockerException as e:
        error_msg = f"Docker connection error: {str(e)}"
        await ctx.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool
async def fetch_docker_image_with_cli_keyword(ctx: Context) -> str:
    """
    Finds and pulls a Docker image using the product keyword provided via CLI.
    This tool is only available when the server is started with a --keyword argument.

    Returns:
        JSON string containing the image name, tag, and pull status.
    """
    if not CLI_PRODUCT_KEYWORD:
        error_msg = "No product keyword was provided via CLI. Use --keyword argument when starting the server."
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})

    return await fetch_docker_image(CLI_PRODUCT_KEYWORD, ctx)


if __name__ == "__main__":
    import argparse

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Docker Tool MCP Server - Manages Docker images and containers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Transport Modes:
    sse (default)     - Server-Sent Events transport for web deployment (default)
    stdio             - Standard input/output transport for local use
    http              - Streamable HTTP transport for web deployment

    Examples:
    python docker_tool.py                                    # Run with SSE transport (default)
    python docker_tool.py --keyword "RHEL 9"                 # Run with SSE and keyword
    python docker_tool.py --stdio                            # Run with stdio transport
    python docker_tool.py --http 127.0.0.1 8000              # Run with HTTP transport
    python docker_tool.py --keyword "Ubuntu 22" --host 0.0.0.0 --port 8001  # Custom config

    Version: %(version)s
        """
        % {"version": VERSION},
    )

    parser.add_argument(
        "--version", action="version", version=f"Docker Tool v{VERSION}"
    )

    # Product keyword argument
    parser.add_argument(
        "--keyword",
        "-k",
        type=str,
        help="Product keyword to search for Docker image (e.g., 'RHEL 9', 'Ubuntu 22'). "
        "When provided, enables the fetch_docker_image_with_cli_keyword tool.",
    )

    # Transport mode arguments
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument(
        "--stdio",
        action="store_true",
        help="Use standard input/output transport for local use",
    )
    transport_group.add_argument(
        "--http",
        action="store_true",
        help="Use streamable HTTP transport for web deployment",
    )
    # Note: SSE is the default, no flag needed

    # Network configuration
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1, only used with SSE/HTTP)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000, only used with SSE/HTTP)",
    )

    try:
        args = parser.parse_args()

        # Set global keyword if provided
        if args.keyword:
            CLI_PRODUCT_KEYWORD = args.keyword
            logger.info("CLI product keyword set to: %s", CLI_PRODUCT_KEYWORD)

        # Determine transport and run server
        if args.stdio:
            logger.info("Starting Docker Tool MCP Server with STDIO transport")
            mcp.run()  # Uses STDIO transport
        elif args.http:
            logger.info(
                "Starting Docker Tool MCP Server with HTTP transport on %s:%s",
                args.host,
                args.port,
            )
            mcp.run(
                transport="streamable-http", host=args.host, port=args.port, path="/mcp"
            )
        else:
            # Default to SSE transport
            logger.info(
                "Starting Docker Tool MCP Server with SSE transport on %s:%s",
                args.host,
                args.port,
            )
            mcp.run(transport="sse", host=args.host, port=args.port)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except (ImportError, ValueError, RuntimeError) as e:
        logger.error("Failed to start server: %s", e)
        sys.exit(1)
