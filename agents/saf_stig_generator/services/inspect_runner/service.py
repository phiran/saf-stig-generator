"""InSpec Runner Tool (mcp/inspec_runner_tool.py):
Propose: Executes InSpec tests against a target and returns results.
https://github.com/inspec/inspec
# RedHat, Ubuntu, and macOS
curl https://chefdownload-commercial.chef.io/install.sh?license_id=<LICENSE_ID> | sudo bash -s -- -P inspec
MCP Tool Name: run_inspec_tests
Returns: The full test results in JSON format.
"""

# agents/src/saf_gen/mcp/inspec_runner_tool.py

import json
import logging
import subprocess

from fastmcp import Context, FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("inspec-runner-tool")
VERSION = "1.0.0"


@mcp.tool
async def run_inspec_tests(profile_path: str, target: str, ctx: Context) -> str:
    """
    Executes an InSpec profile against a target (e.g., a Docker container).
    """
    await ctx.info(f"Running InSpec profile '{profile_path}' against target '{target}'")

    command = ["inspec", "exec", profile_path, "--target", target, "--reporter", "json"]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=600
        )

        # The InSpec JSON output is the last line of stdout
        json_output = result.stdout.strip().splitlines()[-1]

        await ctx.info("InSpec tests completed successfully.")
        return json.dumps({"status": "success", "data": json.loads(json_output)})
    except FileNotFoundError:
        error_msg = "'inspec' command not found. This tool should be run in an environment with Chef InSpec installed."
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})
    except subprocess.CalledProcessError as e:
        error_msg = f"InSpec execution failed. Stderr:\n{e.stderr}"
        await ctx.error(error_msg)
        return json.dumps(
            {"status": "failure", "message": error_msg, "stderr": e.stderr}
        )
    except Exception as e:
        error_msg = f"An unexpected error occurred during InSpec execution: {e}"
        await ctx.error(error_msg)
        return json.dumps({"status": "failure", "message": error_msg})


if __name__ == "__main__":
    mcp.run()
