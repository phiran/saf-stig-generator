"""
DISA STIG Tool (mcp/disa_stig_tool.py):
Purpose: 1. Fetches and extracts STIGs from the DISA website.
[ http://public.cyber.mil/stigs/downloads/ ]
MCP Tool Name: fetch_disa_stig
Returns: A JSON object containing the local path to the extracted XCCDF file and the manual file.
"""

# Suppress websocket deprecation warnings early
import json
import logging
import os
import sys
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import anyio
import requests
from bs4 import BeautifulSoup
from fastmcp import Context, FastMCP

# Environment is automatically loaded by saf_config module
from ...common.config import ensure_dir, get_download_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastMCP Server Initialization ---
mcp = FastMCP("disa-stig-tool")

# --- Constants ---
BASE_URL = "https://public.cyber.mil/stigs/downloads/"
VERSION = "1.0.0"

# Global variable for CLI-provided product keyword
CLI_PRODUCT_KEYWORD = None


def _get_artifacts_download_dir() -> Path:
    """
    Determines the download directory using the saf_config module.
    """
    return get_download_dir()


@mcp.resource("disa-stig-tool://version")
def get_version() -> str:
    """Returns the version of the DISA STIG Tool."""
    return f"DISA STIG Tool v{VERSION}"


@mcp.resource("disa-stig-tool://info")
def get_info() -> dict:
    """Returns information about the DISA STIG Tool."""
    return {
        "name": "DISA STIG Tool",
        "version": VERSION,
        "description": "Downloads and extracts DISA STIG packages from public.cyber.mil",
        "base_url": BASE_URL,
        "supported_formats": [".zip"],
        "output_files": ["XCCDF XML", "Manual XML"],
    }


@mcp.tool
async def fetch_disa_stig(product_keyword: str, ctx: Context) -> str:
    """
    Downloads and extracts an official DISA STIG zip package for a given product.

    Args:
        product_keyword: Keyword to find the product STIG (e.g., 'RHEL 9').

    Returns:
        A JSON string with a 'status' field indicating success or failure.
        On success, the 'data' field contains file paths.
        On failure, the 'message' field contains the error.
    """
    await ctx.info(f"Starting DISA STIG download for: {product_keyword}")
    download_dir = _get_artifacts_download_dir()

    try:
        # 1. Find the STIG download URL
        await ctx.info(f"Searching for STIG matching: {product_keyword}")

        # Run blocking network I/O in a separate thread
        response = await anyio.to_thread.run_sync(
            lambda: requests.get(BASE_URL, timeout=30)
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        stig_url = None
        for a_tag in soup.find_all("a", href=True):
            if product_keyword.lower() in a_tag.text.lower() and a_tag["href"].endswith(
                ".zip"
            ):
                stig_url = urljoin(BASE_URL, a_tag["href"])
                await ctx.info(f"Found STIG download URL: {stig_url}")
                break

        if not stig_url:
            error_msg = (
                f"Could not find a STIG zip file for keyword: '{product_keyword}'"
            )
            await ctx.error(error_msg)
            return json.dumps({"status": "failure", "message": error_msg})

        # 2. Download the zip file
        zip_filename = Path(stig_url).name
        zip_filepath = download_dir / zip_filename
        ensure_dir(download_dir)

        await ctx.info(f"Downloading {zip_filename}...")

        # Use anyio to run the download in a separate thread
        def _download_file():
            with requests.get(stig_url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(zip_filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

        await anyio.to_thread.run_sync(_download_file)

        # 3. Extract the zip file
        extract_path = download_dir / product_keyword.replace(" ", "_").lower()
        await ctx.info(f"Extracting to {extract_path}...")

        with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # 4. Find the necessary files
        xccdf_path, manual_path = None, None
        for root, _, files in os.walk(extract_path):
            for file in files:
                if file.lower().endswith("_manual-xccdf.xml"):
                    xccdf_path = os.path.join(root, file)
                elif "manual" in file.lower() and file.lower().endswith(".xml"):
                    if not file.lower().endswith("_manual-xccdf.xml"):
                        manual_path = os.path.join(root, file)

        if not xccdf_path:
            error_msg = (
                f"Could not find an XCCDF file in the extracted STIG content at "
                f"{extract_path}."
            )
            await ctx.error(error_msg)
            return json.dumps({"status": "failure", "message": error_msg})

        result_paths = {
            "xccdf_path": str(xccdf_path),
            "manual_path": str(manual_path) if manual_path else None,
        }

        await ctx.info("Successfully completed DISA STIG download and extraction.")
        return json.dumps({"status": "success", "data": result_paths})

    except requests.RequestException as e:
        error_msg = f"Network error during download: {e}"
        logger.error(error_msg, exc_info=True)
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})

    except zipfile.BadZipFile as e:
        error_msg = f"Failed to open STIG zip file. It may be corrupt. {e}"
        logger.error(error_msg, exc_info=True)
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})

    except (OSError, IOError, ValueError) as e:
        # Catch file system and other common errors
        error_msg = f"File system or processing error: {e}"
        logger.error("File system error in fetch_disa_stig: %s", e, exc_info=True)
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})


@mcp.tool
async def fetch_disa_stig_with_cli_keyword(stig_keyword: str, ctx: Context) -> str:
    """
    Downloads and extracts a DISA STIG using the provided keyword.

    Args:
        stig_keyword: Keyword to find the product STIG (e.g., 'RHEL 9').

    Returns:
        A JSON string with a 'status' field indicating success or failure.
        On success, the 'data' field contains file paths.
        On failure, the 'message' field contains the error.
    """
    return await fetch_disa_stig.fn(stig_keyword, ctx)


if __name__ == "__main__":
    import argparse

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="DISA STIG Tool MCP Server - Downloads and extracts DISA STIG packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Transport Modes:
    sse (default)     - Server-Sent Events transport for web deployment (default)
    stdio             - Standard input/output transport for local use
    http              - Streamable HTTP transport for web deployment

    Examples:
    python disa_stig_tool.py                                    # Run with SSE transport (default)
    python disa_stig_tool.py --keyword "RHEL 9"                 # Run with SSE and keyword
    python disa_stig_tool.py --stdio                            # Run with stdio transport
    python disa_stig_tool.py --http 127.0.0.1 8000              # Run with HTTP transport
    python disa_stig_tool.py --keyword "Ubuntu 22" --host 0.0.0.0 --port 8001  # Custom config

    Version: %(version)s
        """
        % {"version": VERSION},
    )

    parser.add_argument(
        "--version", action="version", version=f"DISA STIG Tool v{VERSION}"
    )

    # Product keyword argument
    parser.add_argument(
        "--keyword",
        "-k",
        type=str,
        help="Product keyword to search for STIG (e.g., 'RHEL 9', 'Ubuntu 22'). "
        "When provided, enables the fetch_disa_stig_with_cli_keyword tool.",
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
            logger.info("Starting DISA STIG Tool MCP Server with STDIO transport")
            mcp.run()  # Uses STDIO transport
        elif args.http:
            logger.info(
                "Starting DISA STIG Tool MCP Server with HTTP transport on %s:%s",
                args.host,
                args.port,
            )
            mcp.run(
                transport="streamable-http", host=args.host, port=args.port, path="/mcp"
            )
        else:
            # Default to SSE transport
            logger.info(
                "Starting DISA STIG Tool MCP Server with SSE transport on %s:%s",
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
