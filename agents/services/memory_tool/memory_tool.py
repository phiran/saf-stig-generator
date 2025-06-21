"""Memory Tool (mcp/memory_tool.py):
Purpose: Provides an interface to the long-term memory of the system. [ https://docs.trychroma.com/docs/overview/getting-started ]
MCP Tool Name: manage_baseline_memory
Functions:
add_to_memory(baseline_path): Parses a validated baseline and stores its controls in the knowledge store.
query_memory(control_description): Searches the knowledge store for relevant, previously implemented InSpec controls.
"""
import json
import logging
import re
from pathlib import Path
from fastmcp import FastMCP, Context

# You need to add 'chromadb' to your dependencies
try:
    import chromadb
except ImportError:
    print("Error: chromadb is not installed. Please run 'pip install chromadb'")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("memory-tool")
VERSION = "1.0.0"

# --- ChromaDB Client Initialization ---
# This client connects to a running ChromaDB server, which we will define in docker-compose.yml.
# The host 'chromadb' is the service name in the docker-compose network.
try:
    client = chromadb.HttpClient(host="chromadb", port=8000)
    # The collection is where we'll store our InSpec control memories.
    collection = client.get_or_create_collection(name="saf_inspec_controls")
    logger.info("Successfully connected to ChromaDB and got collection 'saf_inspec_controls'.")
except Exception as e:
    logger.error(f"FATAL: Could not connect to ChromaDB. Ensure it is running. Error: {e}")
    client = None
    collection = None

# --- Helper Function to Parse InSpec Files ---
def parse_inspec_controls_from_file(file_content: str) -> list[dict]:
    """
    Parses a string of InSpec code to extract individual controls.
    This uses regex to find control blocks and extract their ID, title, and full code.
    """
    # Regex to capture an entire control block from 'control' to 'end'
    control_pattern = re.compile(r"^(control\s*['\"].*?['\"]\s*do.*?end)$", re.MULTILINE | re.DOTALL)
    # Regex to extract the title from within a control block
    title_pattern = re.compile(r"title\s*['\"](.*?)['\"]")
    # Regex to extract the control ID
    id_pattern = re.compile(r"control\s*['\"](.*?)['\"]")

    found_controls = []
    for match in control_pattern.finditer(file_content):
        control_code = match.group(1).strip()
        
        control_id_match = id_pattern.search(control_code)
        title_match = title_pattern.search(control_code)

        if control_id_match and title_match:
            found_controls.append({
                "id": control_id_match.group(1),
                "description": title_match.group(1),
                "code": control_code
            })
    return found_controls

@mcp.tool
async def add_to_memory(baseline_path: str, ctx: Context) -> str:
    """
    Parses a validated baseline file/directory and stores its controls in the ChromaDB vector store.
    This is how the agent "learns" from successful code.
    """
    if not collection:
        return json.dumps({"status": "failure", "message": "ChromaDB collection is not available."})

    await ctx.info(f"Adding baseline to memory from path: {baseline_path}")
    try:
        p = Path(baseline_path)
        all_controls = []
        
        # In a real SAF profile, controls are often in a 'controls' subdir
        controls_dir = p / 'controls'
        if controls_dir.is_dir():
             target_files = list(controls_dir.glob('*.rb'))
        else:
            target_files = list(p.glob('*.rb'))
        
        if not target_files:
            return json.dumps({"status": "failure", "message": f"No .rb files found in {baseline_path}"})

        for file_path in target_files:
            content = file_path.read_text()
            all_controls.extend(parse_inspec_controls_from_file(content))

        if not all_controls:
            return json.dumps({"status": "success", "message": "No controls found to add."})

        # Add the parsed controls to ChromaDB
        collection.add(
            ids=[c["id"] for c in all_controls],
            documents=[c["description"] for c in all_controls], # The text to be searched/embedded
            metadatas=[{"code": c["code"]} for c in all_controls] # The data we want back
        )
        
        msg = f"Successfully added {len(all_controls)} controls to memory."
        await ctx.info(msg)
        return json.dumps({"status": "success", "controls_added": len(all_controls)})

    except Exception as e:
        error_msg = f"Failed to add baseline to memory: {e}"
        await ctx.error(error_msg, exc_info=True)
        return json.dumps({"status": "failure", "message": error_msg})

@mcp.tool
async def query_memory(control_description: str, n_results: int = 3, ctx: Context) -> str:
    """
    Searches the knowledge store for relevant, previously implemented InSpec controls
    based on a natural language description.
    """
    if not collection:
        return json.dumps({"status": "failure", "message": "ChromaDB collection is not available."})
        
    await ctx.info(f"Querying memory for: '{control_description}'")
    try:
        # Perform the similarity search
        results = collection.query(
            query_texts=[control_description],
            n_results=n_results,
            include=["metadatas"] # We only need the metadata which contains our code
        )
        
        num_found = len(results.get('ids', [[]])[0])
        await ctx.info(f"Found {num_found} results from memory.")

        # The actual data is nested; we extract it here.
        retrieved_metadatas = results.get("metadatas", [[]])[0]
        return json.dumps({"status": "success", "results": retrieved_metadatas})
        
    except Exception as e:
        error_msg = f"Failed to query memory: {e}"
        await ctx.error(error_msg, exc_info=True)
        return json.dumps({"status": "failure", "message": error_msg})

if __name__ == "__main__":
    mcp.run(transport="sse", port=3006)
