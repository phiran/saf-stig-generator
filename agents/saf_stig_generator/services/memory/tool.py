"""Memory Tool (mcp/memory_tool.py):
Purpose: Provides an interface to the long-term memory of the system.
Reference: https://docs.trychroma.com/docs/overview/getting-started
MCP Tool Name: manage_baseline_memory
Functions:
add_to_memory(baseline_path): Parses a validated baseline and stores its
    controls in the knowledge store.
query_memory(control_description): Searches the knowledge store for relevant,
    previously implemented InSpec controls.
"""

import json
import logging
import os
import re
from pathlib import Path

from fastmcp import Context, FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# You need to add 'chromadb' to your dependencies
try:
    import chromadb
except ImportError:
    logger.error("Error: chromadb is not installed. Please run 'pip install chromadb'")
    exit(1)

# --- Configuration ---
CHROMA_DB_PATH = "./artifacts/chroma_db"
# This is the collection for validated code examples.
EXAMPLES_COLLECTION_NAME = "validated_examples"
# This is for documentation.
DOCS_COLLECTION_NAME = "saf_documentation"
# Legacy collection name for backward compatibility
LEGACY_COLLECTION_NAME = "saf_inspec_controls"

mcp = FastMCP("memory-tool")
VERSION = "1.0.0"


@mcp.resource("memory-tool://version")
def get_version() -> str:
    """Returns the version of the Memory Tool."""
    return f"Memory Tool v{VERSION}"


@mcp.resource("memory-tool://info")
def get_info() -> dict:
    """Returns information about the Memory Tool."""
    return {
        "name": "Memory Tool",
        "version": VERSION,
        "description": "Manages long-term memory of InSpec controls using ChromaDB",
        "database": "ChromaDB",
        "collections": {
            "validated_examples": "Pretrained baseline examples",
            "saf_documentation": "SAF documentation",
            "saf_inspec_controls": "Legacy collection",
        },
        "functions": ["add_to_memory", "query_memory", "manage_baseline_memory_mcp"],
        "storage_format": "Vector embeddings",
        "storage_path": CHROMA_DB_PATH,
    }


# --- ChromaDB Client Initialization ---
# Initialize both persistent client for local storage and HTTP client for server-based operations
try:
    # Create the artifacts directory if it doesn't exist
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    # Persistent client for local storage (used by pretrain functionality)
    persistent_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    examples_collection = persistent_client.get_or_create_collection(
        name=EXAMPLES_COLLECTION_NAME
    )

    # HTTP client for server-based operations (legacy support)
    try:
        http_client = chromadb.HttpClient(host="chromadb", port=8000)
        legacy_collection = http_client.get_or_create_collection(
            name=LEGACY_COLLECTION_NAME
        )
        logger.info(
            "Successfully connected to both persistent and HTTP ChromaDB clients."
        )
    except Exception as http_error:
        logger.warning(
            f"HTTP ChromaDB client not available: {http_error}. "
            "Using persistent client only."
        )
        http_client = None
        legacy_collection = None

except Exception as e:
    logger.error(f"FATAL: Could not initialize ChromaDB clients. Error: {e}")
    persistent_client = None
    examples_collection = None
    http_client = None
    legacy_collection = None


# --- Helper Functions ---
def _parse_inspec_control(file_path):
    """
    A simple parser to extract the control ID and title from an InSpec file.
    Returns a dictionary or None if parsing fails.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Find control ID
            control_match = re.search(r"control\s+['\"]([^'\"]+)['\"]", content)
            # Find title
            title_match = re.search(r"title\s+['\"]([^'\"]+)['\"]", content)

            if control_match:
                return {
                    "id": control_match.group(1),
                    "title": title_match.group(1) if title_match else "No title found",
                    "content": content,
                }
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
    return None


def parse_inspec_controls_from_file(file_content: str) -> list[dict]:
    """
    Parses a string of InSpec code to extract individual controls.
    This uses regex to find control blocks and extract their ID, title, and full code.
    """
    # Regex to capture an entire control block from 'control' to 'end'
    control_pattern = re.compile(
        r"^(control\s*['\"].*?['\"]\s*do.*?end)$", re.MULTILINE | re.DOTALL
    )
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
            found_controls.append(
                {
                    "id": control_id_match.group(1),
                    "description": title_match.group(1),
                    "code": control_code,
                }
            )
    return found_controls


def manage_baseline_memory(
    action: str, baseline_path: str = None, query_text: str = None
):
    """
    Manages the 'validated_examples' knowledge store.
    Actions:
    - 'add': Ingests all InSpec controls from a local directory path.
    - 'query': Searches for relevant control examples.
    """
    if not examples_collection:
        return {
            "status": "error",
            "message": "ChromaDB examples collection is not available.",
        }

    if action == "add":
        if not baseline_path or not os.path.isdir(baseline_path):
            return {
                "status": "error",
                "message": "A valid directory path must be provided for the 'add' action.",
            }

        documents = []
        metadatas = []
        ids = []

        logger.info(f"Starting ingestion from directory: {baseline_path}")
        # Walk through the directory to find all .rb files
        for root, _, files in os.walk(baseline_path):
            for file in files:
                if file.endswith(".rb"):
                    file_path = os.path.join(root, file)
                    parsed_control = _parse_inspec_control(file_path)
                    if parsed_control:
                        # The document is the full code content
                        documents.append(parsed_control["content"])
                        # Metadata helps with filtering and provides context
                        metadatas.append(
                            {
                                "source": baseline_path,
                                "control_id": parsed_control["id"],
                            }
                        )
                        # Ensure unique IDs
                        ids.append(f"{baseline_path}:{parsed_control['id']}:{file}")

        if not documents:
            return {
                "status": "warning",
                "message": "No .rb control files found in the specified path.",
            }

        examples_collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return {
            "status": "success",
            "message": f"Added {len(documents)} controls to memory from {baseline_path}.",
        }

    elif action == "query":
        if not query_text:
            return {
                "status": "error",
                "message": "Query text must be provided for the 'query' action.",
            }

        results = examples_collection.query(query_texts=[query_text], n_results=5)
        # Return a list of the code examples (the documents)
        return {
            "status": "success",
            "results": (
                results["documents"][0] if results and results["documents"] else []
            ),
        }

    else:
        return {
            "status": "error",
            "message": f"Invalid action '{action}'. Must be 'add' or 'query'.",
        }


@mcp.tool
async def manage_baseline_memory_mcp(
    action: str, baseline_path: str = None, query_text: str = None, ctx: Context = None
) -> str:
    """
    MCP interface for managing baseline memory.
    Actions:
    - 'add': Ingests all InSpec controls from a local directory path.
    - 'query': Searches for relevant control examples.
    """
    if ctx:
        await ctx.info(f"Managing baseline memory with action: {action}")

    result = manage_baseline_memory(action, baseline_path, query_text)
    return json.dumps(result)


@mcp.tool
async def add_to_memory(baseline_path: str, ctx: Context) -> str:
    """
    Parses a validated baseline file/directory and stores its controls in the ChromaDB vector store.
    This is how the agent "learns" from successful code.
    Uses the legacy collection for backward compatibility.
    """
    # Try to use legacy collection first, fall back to examples collection
    target_collection = legacy_collection if legacy_collection else examples_collection

    if not target_collection:
        return json.dumps(
            {"status": "failure", "message": "ChromaDB collection is not available."}
        )

    await ctx.info(f"Adding baseline to memory from path: {baseline_path}")
    try:
        p = Path(baseline_path)
        all_controls = []

        # In a real SAF profile, controls are often in a 'controls' subdir
        controls_dir = p / "controls"
        if controls_dir.is_dir():
            target_files = list(controls_dir.glob("*.rb"))
        else:
            target_files = list(p.glob("*.rb"))

        if not target_files:
            return json.dumps(
                {
                    "status": "failure",
                    "message": f"No .rb files found in {baseline_path}",
                }
            )

        for file_path in target_files:
            content = file_path.read_text()
            all_controls.extend(parse_inspec_controls_from_file(content))

        if not all_controls:
            return json.dumps(
                {"status": "success", "message": "No controls found to add."}
            )

        # Add the parsed controls to ChromaDB
        target_collection.add(
            ids=[c["id"] for c in all_controls],
            documents=[
                c["description"] for c in all_controls
            ],  # The text to be searched/embedded
            metadatas=[
                {"code": c["code"]} for c in all_controls
            ],  # The data we want back
        )

        msg = f"Successfully added {len(all_controls)} controls to memory."
        await ctx.info(msg)
        return json.dumps({"status": "success", "controls_added": len(all_controls)})

    except Exception as e:
        error_msg = f"Failed to add baseline to memory: {e}"
        await ctx.error(error_msg, exc_info=True)
        return json.dumps({"status": "failure", "message": error_msg})


@mcp.tool
async def query_memory(
    control_description: str, ctx: Context, n_results: int = 3
) -> str:
    """
    Searches the knowledge store for relevant, previously implemented InSpec controls
    based on a natural language description.
    Uses the legacy collection first, falls back to examples collection.
    """
    # Try to use legacy collection first, fall back to examples collection
    target_collection = legacy_collection if legacy_collection else examples_collection

    if not target_collection:
        return json.dumps(
            {"status": "failure", "message": "ChromaDB collection is not available."}
        )

    await ctx.info(f"Querying memory for: '{control_description}'")
    try:
        # Perform the similarity search
        results = target_collection.query(
            query_texts=[control_description],
            n_results=n_results,
            include=["metadatas"],  # We only need the metadata which contains our code
        )

        num_found = len(results.get("ids", [[]])[0])
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
