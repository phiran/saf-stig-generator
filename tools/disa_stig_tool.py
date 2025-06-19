# tools/disa_stig_tool.py
import logging
import contextlib
from collections.abc import AsyncIterator

import uvicorn
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

    # --- TODO: Implement actual web scraping and download logic here ---
    # This involves:
    # 1. Scraping public.cyber.mil/stigs/downloads/
    # 2. Finding the correct zip file link.
    # 3. Downloading the zip file.
    # 4. Extracting it to the artifacts/downloads directory.
    # 5. Finding the XCCDF file within the extracted contents.

    await ctx.session.send_log_message(level="info", data={"status": "complete"})

    # Return the path to the extracted files
    # This is a dummy response for now.
    dummy_response = {
        "xccdf_path": f"artifacts/downloads/{product}/U_XYZ_V1R1_Manual-xccdf.xml",
        "manual_path": f"artifacts/downloads/{product}/U_XYZ_V1R1_Manual.html",
    }

    return [types.TextContent(text=str(dummy_response))]


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
