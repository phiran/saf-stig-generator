"""SAF Generator Tool (mcp/saf_generator_tool.py):
Propose:  Wraps the saf CLI to create InSpec stubs. [ https://saf-cli.mitre.org/ ]
https://saf-cli.mitre.org/#installation-via-npm
npm install -g @mitre/saf
MCP Tool Name: generate_saf_stub
Returns: A JSON object with the path to the newly created baseline stub directory."""

# agents/src/saf_gen/mcp/saf_generator_tool.py

import json
import logging
import subprocess
from pathlib import Path

from fastmcp import Context, FastMCP

from saf_config import ensure_dir, get_generated_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("saf-generator-tool")
VERSION = "1.0.0"


@mcp.tool
async def generate_saf_stub(xccdf_path: str, ctx: Context) -> str:
    """
    Wraps the @mitre/saf CLI to generate InSpec stubs from a DISA XCCDF file.
    """
    await ctx.info(f"Generating InSpec stub for: {xccdf_path}")

    generated_dir = get_generated_dir()
    ensure_dir(generated_dir)

    # Create a unique output directory for the generated stub
    xccdf_filename = Path(xccdf_path).stem
    output_dir = generated_dir / f"{xccdf_filename}_stub"

    command = [
        "saf",
        "generate",
        "stig",
        "--input",
        xccdf_path,
        "--output",
        str(output_dir),
    ]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=300
        )
        await ctx.info(f"Successfully generated stub at: {output_dir}")
        logger.info(f"SAF CLI output:\n{result.stdout}")
        return json.dumps({"status": "success", "data": {"stub_path": str(output_dir)}})
    except FileNotFoundError:
        error_msg = "'saf' command not found. Make sure @mitre/saf is installed globally (`npm install -g @mitre/saf`)."
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to generate stub. SAF CLI exited with error:\n{e.stderr}"
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})


if __name__ == "__main__":
    mcp.run()
    logger.info(f"Running SAF Generator Tool (version {VERSION})")
