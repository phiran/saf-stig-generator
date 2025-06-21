"""Memory Tool (mcp/memory_tool.py):
Purpose: Provides an interface to the long-term memory of the system. [ https://docs.trychroma.com/docs/overview/getting-started ]
MCP Tool Name: manage_baseline_memory
Functions:
add_to_memory(baseline_path): Parses a validated baseline and stores its controls in the knowledge store.
query_memory(control_description): Searches the knowledge store for relevant, previously implemented InSpec controls.
"""
import json
import logging
import chromadb
from pathlib import Path
from fastmcp import FastMCP, Context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("memory-tool")
VERSION = "1.0.0"

# --- ChromaDB Client Initialization ---
# This client connects to a running ChromaDB server,
# which we will define in docker-compose.yml.
try:
    client = chromadb.HttpClient(host="chromadb", port=8000)
    collection = client.get_or_create_collection(name="saf_inspec_controls")
    logger.info("Successfully connected to ChromaDB and got collection 'saf_inspec_controls'.")
except Exception as e:
    logger.error(f"Failed to connect to ChromaDB. Ensure it is running. Error: {e}")
    client = None
    collection = None

# --- Helper Function ---
def parse_inspec_controls(file_path: Path) -> list:
    """
    A simple parser to extract control info from an InSpec Ruby file.
    NOTE: This is a basic example. A more robust solution might use a Ruby parser
    or more advanced regex.
    """
    # This function needs to be implemented based on the actual structure
    # of your InSpec files. For now, we'll assume a simple placeholder.
    # In a real scenario, you'd parse the title, desc, and code for each control.
    logger.warning("Using placeholder InSpec parser. This should be implemented properly.")
    return [
        {
            "id": "V-230222",
            "description": "RHEL 9 must be a supported release.",
            "code": "control 'V-230222'\n  title 'The RHEL 9 operating system must be a supported release.'\n  # ... more code ...\nend"
        }
    ]


@mcp.tool
async def add_to_memory(baseline_path: str, ctx: Context) -> str:
    """
    Parses a validated baseline and stores its controls in the ChromaDB store.
    """
    if not collection:
        return json.dumps({"status": "failure", "message": "ChromaDB collection not available."})

    await ctx.info(f"Adding baseline to memory from: {baseline_path}")
    try:
        # In a real implementation, you'd iterate over all .rb files
        controls = parse_inspec_controls(Path(baseline_path))

        if not controls:
            return json.dumps({"status": "success", "message": "No controls found to add."})

        collection.add(
            ids=[c["id"] for c in controls],
            documents=[c["description"] for c in controls],
            metadatas=[{"code": c["code"]} for c in controls]
        )
        await ctx.info(f"Successfully added {len(controls)} controls to memory.")
        return json.dumps({"status": "success", "controls_added": len(controls)})

    except Exception as e:
        error_msg = f"Failed to add baseline to memory: {e}"
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})

@mcp.tool
async def query_memory(control_description: str, n_results: int = 3, ctx: Context) -> str:
    """
    Searches the knowledge store for relevant, previously implemented InSpec controls.
    """
    if not collection:
        return json.dumps({"status": "failure", "message": "ChromaDB collection not available."})
        
    await ctx.info(f"Querying memory for: '{control_description}'")
    try:
        results = collection.query(
            query_texts=[control_description],
            n_results=n_results
        )
        await ctx.info(f"Found {len(results.get('ids', [[]])[0])} results from memory.")
        # Return only the metadata (which contains the code)
        return json.dumps({"status": "success", "results": results.get("metadatas", [])[0]})
        
    except Exception as e:
        error_msg = f"Failed to query memory: {e}"
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})

if __name__ == "__main__":
    mcp.run()