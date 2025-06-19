import os
import json
import logging
import contextlib
import zipfile
from collections.abc import AsyncIterator
from urllib.parse import urljoin

import anyio
import requests
import uvicorn
from bs4 import BeautifulSoup

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- MCP Server Initialization ---
app = Server("disa-stig-tool")


def _find_and_download_stig(product_keyword: str, download_dir: str, session):
    """
    Synchronous helper function to perform the web scraping, downloading,
    and extraction. Runs in a separate thread to avoid blocking the server.
    """
    base_url = "https://public.cyber.mil/stigs/downloads/"
    stig_url = None

    # 1. Scraping public.cyber.mil to find the link
    logger.info(f"Scraping {base_url} for '{product_keyword}'...")
    response = requests.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    for a_tag in soup.find_all("a", href=True):
        if product_keyword.lower() in a_tag.text.lower() and a_tag["href"].endswith(
            ".zip"
        ):
            stig_url = urljoin(base_url, a_tag["href"])
            logger.info(f"Found matching STIG URL: {stig_url}")
            break

    if not stig_url:
        raise FileNotFoundError(
            f"Could not find a STIG zip file for keyword: '{product_keyword}'"
        )

    # 2. Downloading the zip file
    zip_filename = os.path.basename(stig_url)
    zip_filepath = os.path.join(download_dir, zip_filename)
    os.makedirs(download_dir, exist_ok=True)

    logger.info(f"Downloading {zip_filename} to {zip_filepath}...")
    with requests.get(stig_url, stream=True) as r:
        r.raise_for_status()
        with open(zip_filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # 3. Extracting the zip file
    # Create a directory named after the product to avoid file collisions
    extract_path = os.path.join(download_dir, product_keyword.replace(" ", "_").lower())
    logger.info(f"Extracting {zip_filename} to {extract_path}...")
    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    # 4. Finding the XCCDF and manual files
    xccdf_path, manual_path = None, None
    for root, _, files in os.walk(extract_path):
        for file in files:
            # Typically the XCCDF file ends like this
            if file.lower().endswith("_manual-xccdf.xml"):
                xccdf_path = os.path.join(root, file)
            # The manual is often an XML file as well, check for a common pattern
            elif "manual" in file.lower() and file.lower().endswith(".xml"):
                # Avoid assigning the xccdf file to the manual path
                if not file.lower().endswith("_manual-xccdf.xml"):
                    manual_path = os.path.join(root, file)

    if not xccdf_path:
        raise FileNotFoundError(
            f"Could not find an XCCDF file in the extracted STIG content at {extract_path}."
        )

    logger.info(f"Found XCCDF at: {xccdf_path}")
    logger.info(f"Found Manual at: {manual_path}")

    return {"xccdf_path": xccdf_path, "manual_path": manual_path}


# --- Tool Definitions ---
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """Declares the 'fetch_disa_stig' tool."""
    return [
        types.Tool(
            name="fetch_disa_stig",
            description="Downloads and extracts an official DISA STIG zip package for a given product.",
            input_schema={
                "type": "object",
                "properties": {
                    "product_keyword": {
                        "type": "string",
                        "description": "Keyword to find the product STIG (e.g., 'RHEL 9').",
                    },
                },
                "required": ["product_keyword"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.Content]:
    """Handles the execution of the 'fetch_disa_stig' tool."""
    ctx = app.request_context
    if name != "fetch_disa_stig":
        return [types.TextContent(text=f"Unknown tool: {name}")]

    product = arguments.get("product_keyword")
    await ctx.session.send_log_message(
        level="info", data={"status": "starting", "product": product}
    )

    # Define download directory from environment or default
    download_dir = os.getenv("ARTIFACTS_DIR", "artifacts/downloads")

    try:
        # Run the synchronous helper function in a worker thread
        result_paths = await anyio.to_thread.run_sync(
            _find_and_download_stig, product, download_dir, ctx.session
        )

        await ctx.session.send_log_message(
            level="info", data={"status": "complete", "paths": result_paths}
        )
        return [types.TextContent(text=json.dumps(result_paths))]

    except Exception as e:
        logger.error(f"Error in call_tool for fetch_disa_stig: {e}", exc_info=True)
        await ctx.session.send_log_message(
            level="error", data={"status": "failed", "error": str(e)}
        )
        return [types.TextContent(text=json.dumps({"error": str(e)}))]


# --- Starlette Application Setup ---
session_manager = StreamableHTTPSessionManager(app=app, stateless=True)


async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope, receive, send)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with session_manager.run():
        logger.info("DISA STIG Tool MCP Server started.")
        yield


starlette_app = Starlette(
    debug=True, routes=[Mount("/mcp", app=handle_streamable_http)], lifespan=lifespan
)

if __name__ == "__main__":
    uvicorn.run(starlette_app, host="0.0.0.0", port=3000)
    logger.info("DISA STIG Tool MCP Server is running.")
