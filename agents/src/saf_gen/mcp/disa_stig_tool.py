"""
DISA STIG Tool (mcp/disa_stig_tool.py):
Purpose: Fetches and extracts STIGs from the DISA website. [ https://public.cyber.mil/stigs/downloads/ ]
MCP Tool Name: fetch_disa_stig
Returns: A JSON object containing the local path to the extracted XCCDF file and the manual file.
"""

import os
import json
import logging
import zipfile
from urllib.parse import urljoin
from pathlib import Path

import anyio
import requests
from bs4 import BeautifulSoup
from fastmcp import FastMCP, Context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastMCP Server Initialization ---
mcp = FastMCP("disa-stig-tool")

# --- Constants ---
BASE_URL = "https://public.cyber.mil/stigs/downloads/"
VERSION = "1.0.0"


def _get_artifacts_download_dir() -> Path:
    """
    Determines the download directory.
    Priority:
    1. ARTIFACTS_DIR environment variable.
    2. A directory named 'artifacts/downloads' located two levels
       above this script's location.
    """
    if artifacts_dir_env := os.getenv("ARTIFACTS_DIR"):
        return Path(artifacts_dir_env)

    # Path to the current script -> up two levels -> 'artifacts/downloads'
    script_path = Path(__file__).resolve()
    base_dir = script_path.parent.parent
    return base_dir / "artifacts" / "downloads"


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
        os.makedirs(download_dir, exist_ok=True)

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
            error_msg = f"Could not find an XCCDF file in the extracted STIG content at {extract_path}."
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


if __name__ == "__main__":
    import sys
    import argparse

    # Create argument parser
    parser = argparse.ArgumentParser(
        description="DISA STIG Tool MCP Server - Downloads and extracts DISA STIG packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Transport Modes:
    stdio (default)    - Standard input/output transport for local use
    sse               - Server-Sent Events transport for web deployment  
    http              - Streamable HTTP transport for web deployment

    Examples:
    python disa_stig_tool.py                           # Run with stdio transport
    python disa_stig_tool.py --sse                     # Run with SSE on default host/port
    python disa_stig_tool.py --sse 0.0.0.0 8001        # Run with SSE on specific host/port
    python disa_stig_tool.py --http 127.0.0.1 8000     # Run with HTTP transport

    Version: %(version)s
        """
        % {"version": VERSION},
    )

    parser.add_argument(
        "--version", action="version", version=f"DISA STIG Tool v{VERSION}"
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
                "Starting DISA STIG Tool MCP Server with SSE transport on %s:%s",
                args.host,
                args.port,
            )
            mcp.run(transport="sse", host=args.host, port=args.port)
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
            logger.info("Starting DISA STIG Tool MCP Server with STDIO transport")
            mcp.run()  # Default: uses STDIO transport

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to start server: %s", e)
        sys.exit(1)
